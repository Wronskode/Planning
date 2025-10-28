import streamlit as st
import minizinc
import pandas as pd
import datetime
import subprocess
import os
import tarfile
import requests
from pathlib import Path
import sys
from random import randint

MINIZINC_VERSION = "2.9.4"
MINIZINC_INSTALL_DIR = Path("/tmp/minizinc_install")
archive_name = f"MiniZincIDE-{MINIZINC_VERSION}-bundle-linux-x86_64.tgz"
download_url = f"https://github.com/MiniZinc/MiniZincIDE/releases/download/{MINIZINC_VERSION}/{archive_name}"
MINIZINC_BUNDLE_DIR_NAME = f"MiniZincIDE-{MINIZINC_VERSION}-bundle-linux-x86_64"
MINIZINC_EXECUTABLE = MINIZINC_INSTALL_DIR / MINIZINC_BUNDLE_DIR_NAME / "bin" / "minizinc"

matieres = [
    "EnseignementScientifique", "Anglais", "Espagnol", "Mathematiques",
    "HistoireGeographie", "Physique", "EPS", "Philosophie", "Option"
]
matieres_map = {name: i for i, name in enumerate(matieres)}
matieres_map_affectations = {0: "Pas d'affectation spécifique"}
for i, name in enumerate(matieres):
    matieres_map_affectations[i+1] = name 

if 'minizinc_result' not in st.session_state:
    st.session_state.minizinc_result = None

@st.cache_resource
def setup_minizinc(version, install_dir, executable_path, archive_name_arg, download_url_arg):
    if executable_path.exists():
        try: subprocess.run(['chmod', '+x', str(executable_path)], check=True, timeout=5)
        except Exception: pass
        return executable_path
    install_dir.mkdir(parents=True, exist_ok=True)
    archive_path = install_dir / archive_name_arg
    try:
        with st.spinner(f"Téléchargement de MiniZinc {version}..."):
            with requests.get(download_url_arg, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(archive_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192*4): f.write(chunk)
        with st.spinner(f"Extraction de MiniZinc {version}..."):
             with tarfile.open(archive_path, "r:gz") as tar: tar.extractall(path=install_dir)
        if archive_path.exists(): archive_path.unlink()
        if executable_path.exists():
            subprocess.run(['chmod', '+x', str(executable_path)], check=True, timeout=5)
            return executable_path
        else:
            st.error(f"Exécutable MiniZinc introuvable: {executable_path}")
            return None
    except Exception as e:
        st.error(f"Échec install MiniZinc: {e}")
        return None

minizinc_exe_path_obj = setup_minizinc(MINIZINC_VERSION, MINIZINC_INSTALL_DIR, MINIZINC_EXECUTABLE, archive_name, download_url)
solver = None
if minizinc_exe_path_obj:
    try:
        driver = minizinc.Driver(minizinc_exe_path_obj)
        minizinc.default_driver = driver
        try:
             result_ver = subprocess.run([str(minizinc_exe_path_obj), '--version'], capture_output=True, text=True, check=True, timeout=10)
        except Exception:
             st.sidebar.warning("Impossible de vérifier version MiniZinc.")
        solver = minizinc.Solver.lookup("cp-sat")
    except Exception as e:
        st.error(f"Erreur config driver/solveur: {e}")
        st.stop()
else:
    st.error("Échec install MiniZinc.")
    st.stop()
st.set_page_config(layout="wide")
st.title("Solveur d'Emploi du Temps 📅")

with st.sidebar:
    st.header("Paramètres du Problème")
    timeout_secondes = st.slider("Timeout (sec)", 5, 600, 5, 5)
    nombre_heures_jour_input = st.number_input("Heures/jour", 4, 12, 10, 1)
    nombre_profs_input = st.number_input("Nb Profs (pool)", 5, 50, 11, 1)
    num_classes_input = st.number_input("Nb Classes", 1, 10, 3, 1)

    tailles_classes_input = []
    st.subheader("Capacité Classes")
    default_tailles = [randint(25, 33) for _ in range(num_classes_input)]
    for i in range(num_classes_input):
        size = st.number_input(f"Taille Classe {i+1}", 15, 40, default_tailles[i], 1, key=f"tcl_{i}")
        tailles_classes_input.append(size)

    salles_enum_list = ["S101","S102","S201","S202","S203","S204","Gymnase","Stade","LaboPhysique1","LaboPhysique2","LaboChimie","Empty"]
    capacites_salles_input = []
    st.subheader("Capacité Salles")
    default_caps = [35, 35, 31, 30, 32, 29, 60, 100, 32, 32, 34, 0]
    for i, name in enumerate(salles_enum_list):
        if name == "Empty": capacites_salles_input.append(0); continue
        cap = st.number_input(f"Capacité {name}", 0, 150, default_caps[i], 1, key=f"csal_{name}")
        capacites_salles_input.append(cap)

    st.subheader("Indisponibilités Profs")
    dj_opts = {0:"Dispo", 1:"Lu Ma", 2:"Lu Ap", 3:"Ma Ma", 4:"Ma Ap", 5:"Me Ma", 7:"Je Ma", 8:"Je Ap", 9:"Ve Ma", 10:"Ve Ap"}
    interdictions_input = []
    for i in range(nombre_profs_input):
        sel = st.selectbox(f"P{i+1}", list(dj_opts.keys()), format_func=lambda x: dj_opts[x], key=f"int_{i}")
        interdictions_input.append(sel)

    st.subheader("Affectations Spécifiques Profs")
    affectations_input_raw = []
    affectations_input_mzn = []
    for i in range(nombre_profs_input):
        sel_idx = st.selectbox(f"P{i+1}", list(matieres_map_affectations.keys()), format_func=lambda x: matieres_map_affectations[x], key=f"aff_{i}")
        affectations_input_raw.append(sel_idx)
        affectations_input_mzn.append(matieres_map_affectations[sel_idx] if sel_idx > 0 else "Void")

# --- Bouton de Lancement et Logique de Résolution ---
if st.button(f"Lancer la résolution ({num_classes_input} classes, max {timeout_secondes} sec)", icon="▶️"):
    if solver is None: st.error("Solveur non configuré."); st.stop()

    try:
        model = minizinc.Model("./planning.mzn")
        inst = minizinc.Instance(solver, model)
        inst["CLASS"] = range(1, num_classes_input + 1)
        inst["taille_classe"] = tailles_classes_input
        inst["PROFS"] = range(1, nombre_profs_input + 1)
        inst["nombre_heures_jour"] = nombre_heures_jour_input
        inst["DAY"] = range(1, nombre_heures_jour_input + 1)
        inst["WEEK"] = range(1, 5 + 1)
        inst["capacite_salle"] = capacites_salles_input
        inst["interdictions"] = interdictions_input
        inst["affectations"] = affectations_input_mzn

    except Exception as e: st.error(f"Erreur création instance: {e}"); st.stop()

    result_placeholder = st.empty()
    with st.spinner(f"Calcul en cours... ({num_classes_input} classes, max {timeout_secondes}s)"):
        solve_result = None
        try:
            try:
                import ortools
                ortools_dir = Path(ortools.__file__).parent
                lib_paths = [str(p) for p in [ortools_dir, ortools_dir / ".libs"] if p.is_dir()]
                if lib_paths:
                    ld_path = os.environ.get('LD_LIBRARY_PATH', '')
                    new_ld = ":".join(lib_paths)
                    if ld_path: new_ld = new_ld + ":" + ld_path
                    os.environ['LD_LIBRARY_PATH'] = new_ld
            except Exception: pass

            solve_result = inst.solve(
                processes=8,
                timeout=datetime.timedelta(seconds=timeout_secondes)
            )
            st.session_state.minizinc_result = solve_result

        except Exception as e:
            st.session_state.minizinc_result = None
            st.error(f"Erreur pendant la résolution: {e}")
            st.exception(e)
st.header("Résultat de la résolution")

if st.session_state.minizinc_result is not None:
    result = st.session_state.minizinc_result

    if result and result.solution:
        status_message = f"Statut: {result.status}"
        if result.status == minizinc.Status.OPTIMAL_SOLUTION: st.success(f"🎉 Optimal! ({status_message})")
        elif result.status == minizinc.Status.SATISFIED: st.warning(f"⚠️ Timeout! Meilleure solution. ({status_message})")
        else: st.info(f"Terminé. ({status_message})")

        st.info(f"Score objectif = {result.objective}")
        solution = result.solution

        jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
        nombre_heures = 0
        heures = [] # Sera défini plus bas

        def style_cell_html(cell_value):
            if not cell_value or cell_value == "": return '<span style="color: #555;"></span>'
            lines = cell_value.split('\n')
            matiere = lines[0]
            color = "#FAFAFA"; weight = "normal"
            if matiere in ["Mathematiques","Physique","EnseignementScientifique"]: color="#87CEFA"; weight="bold"
            elif matiere in ["Anglais","Espagnol"]: color="#90EE90"
            elif matiere in ["HistoireGeographie","Philosophie"]: color="#FFDAB9"
            elif matiere in ["EPS","Option"]: color="#D8BFD8"
            html_content = cell_value.replace('\n', '<br>')
            return f'<span style="color: {color}; font-weight: {weight};">{html_content}</span>'

        # Planning Classe
        if hasattr(solution, "planning"):
            planning_data = solution.planning
            num_classes_sol = len(planning_data)
            if num_classes_sol > 0 and planning_data[0] is not None and len(planning_data[0]) > 0:
                nombre_heures = len(planning_data[0])
                heures = [f"H{d} ({d+7}h)" for d in range(1, nombre_heures + 1)]
                planning_salle_data = getattr(solution, "planning_salle", None)
                prof_to_class_data = getattr(solution, "prof_to_class", None)
                prefs_data = getattr(solution, "prefs", None)
                obj_prof_used_value = sum(getattr(solution, "prof_est_utilise", [0]))
                profs_indices = range(obj_prof_used_value)

                st.header("Plannings par Classe")
                for c in range(num_classes_sol):
                    st.subheader(f"Classe {c+1}")
                    planning_display_list = [["" for _ in jours] for _ in range(nombre_heures)]
                    for d in range(nombre_heures):
                        for w in range(len(jours)):
                            cell_text_raw = ""
                            if c<len(planning_data) and d<len(planning_data[c]) and w<len(planning_data[c][d]):
                                matiere_obj = planning_data[c][d][w]
                                if matiere_obj is not None:
                                     matiere_name = str(matiere_obj)
                                     if matiere_name != "Void":
                                         salle_name = ""
                                         prof_name = ""
                                         if planning_salle_data and c<len(planning_salle_data) and d<len(planning_salle_data[c]) and w<len(planning_salle_data[c][d]):
                                             salle_obj = planning_salle_data[c][d][w]
                                             if salle_obj is not None and str(salle_obj) != "Empty": salle_name = str(salle_obj)
                                         if prof_to_class_data and prefs_data and matiere_name in matieres_map:
                                             matiere_index = matieres_map[matiere_name]
                                             for p_index in profs_indices:
                                                 if p_index<len(prof_to_class_data) and c<len(prof_to_class_data[p_index]) and \
                                                    prof_to_class_data[p_index][c]==1 and p_index<len(prefs_data) and \
                                                    matiere_index<len(prefs_data[p_index]) and prefs_data[p_index][matiere_index]==1:
                                                     prof_name = f"P{p_index+1}"; break
                                         cell_text_raw = matiere_name
                                         if prof_name: cell_text_raw += f"\n({prof_name})"
                                         if salle_name: cell_text_raw += f"\n[{salle_name}]"
                            planning_display_list[d][w] = style_cell_html(cell_text_raw)
                    df = pd.DataFrame(planning_display_list, columns=jours, index=heures)
                    st.markdown(df.to_html(escape=False, index=True), unsafe_allow_html=True)
            else: st.warning("Données planning vides.")
        else: st.warning("Variable 'planning' non trouvée.")

        if not heures:
             try:
                 nombre_heures_mzn = inst["nombre_heures_jour"]
                 if nombre_heures_mzn > 0: nombre_heures=nombre_heures_mzn; heures=[f"H{d}({d+7}h)" for d in range(1, nombre_heures + 1)]
                 else: st.error("Nb heures invalide."); st.stop()
             except KeyError: st.error("'nombre_heures_jour' manquant."); st.stop()

        # Professeurs
        if (hasattr(solution, "prof_est_utilise") and hasattr(solution, "prefs") and
            hasattr(solution, "planning_prof") and hasattr(solution, "planning") and
            'planning_data' in locals() and hasattr(solution, "prof_to_class") and heures):

            obj_prof_used_value = sum(solution.prof_est_utilise)
            prefs_data = solution.prefs
            prof_to_class_data = solution.prof_to_class
            num_classes_sol = len(planning_data)
            st.header(f"Recrutement & Plannings ({obj_prof_used_value} professeurs)")
            profs_indices = range(obj_prof_used_value)

            prefs_display = []
            for p_index in profs_indices:
                competences = []
                if p_index < len(prefs_data):
                    if prefs_data[p_index] is not None and len(prefs_data[p_index]) > len(matieres):
                        for i in range(len(matieres)):
                            if prefs_data[p_index][i] == 1: competences.append(matieres[i])
                if not competences: competences = ["(Aucune)"]
                prefs_display.append(f"Prof P{p_index+1} : {', '.join(competences)}")
            st.subheader("Compétences recrutées:"); st.text("\n".join(prefs_display))

            st.subheader("Plannings professeurs:")
            for p_index in profs_indices:
                st.write(f"**Prof P{p_index+1}**")
                prof_schedule_display = [["" for _ in jours] for _ in range(nombre_heures)]
                for d in range(nombre_heures):
                    for w in range(len(jours)):
                        for c in range(num_classes_sol):
                            if c<len(planning_data) and d<len(planning_data[c]) and w<len(planning_data[c][d]):
                                matiere_obj = planning_data[c][d][w]
                                if matiere_obj is not None:
                                    if p_index<len(prof_to_class_data) and c<len(prof_to_class_data[p_index]):
                                        is_assigned = (prof_to_class_data[p_index][c] == 1)
                                        if not is_assigned: continue
                                    matiere_name = str(matiere_obj)
                                    if matiere_name in matieres_map:
                                        matiere_index = matieres_map[matiere_name]
                                        if p_index<len(prefs_data) and matiere_index<len(prefs_data[p_index]):
                                            is_competent = (prefs_data[p_index][matiere_index] == 1)
                                            if is_competent: prof_schedule_display[d][w] = f"Classe {c+1}"; break
                df = pd.DataFrame(prof_schedule_display, columns=jours, index=heures)
                config = {jour: st.column_config.TextColumn(width="small") for jour in jours} # smaller width
                st.dataframe(df, column_config=config, use_container_width=True)
        else:
            st.warning("Variables profs incomplètes pour plannings.")

        # Salles
        if hasattr(solution, "planning_salle") and heures:
            st.header("Occupation Salles")
            salles_list_display = [s for s in salles_enum_list if s != "Empty"]
            room_schedules = {salle: [["" for _ in jours] for _ in range(nombre_heures)] for salle in salles_list_display}
            planning_salle_data = solution.planning_salle
            num_classes_sol = len(planning_salle_data)
            num_jours = len(jours)
            for c in range(num_classes_sol):
                for d in range(nombre_heures):
                    for w in range(num_jours):
                         if c<len(planning_salle_data) and d<len(planning_salle_data[c]) and w<len(planning_salle_data[c][d]):
                            salle_obj = planning_salle_data[c][d][w]
                            if salle_obj is not None:
                                salle_name = str(salle_obj)
                                if salle_name != "Empty" and salle_name in room_schedules:
                                    room_schedules[salle_name][d][w] = f"Classe {c+1}"
            for salle_name, schedule_data in room_schedules.items():
                st.subheader(f"Salle: {salle_name}")
                df = pd.DataFrame(schedule_data, columns=jours, index=heures)
                config = {jour: st.column_config.TextColumn(width="small") for jour in jours} # smaller width
                st.dataframe(df, column_config=config, use_container_width=True)
        else:
            st.warning("Variable 'planning_salle' non trouvée.")

    elif result and result.status == minizinc.Status.UNSATISFIABLE:
        st.error(f"UNSAT avec ces paramètres. Statut: {result.status}")
    elif result:
        st.error(f"Pas de solution retournée. Statut: {result.status}")
    else:
        st.error("Résolution échouée ou aucun résultat (réessayez en augmentant le timeout ?)")
elif 'minizinc_result' not in st.session_state or st.session_state.minizinc_result is None:
    if not st.session_state.get("solve_error", False):
         st.info("Configurez les paramètres et lancez la résolution.")