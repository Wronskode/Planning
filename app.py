import streamlit as st
import minizinc
import pandas as pd
import datetime
import subprocess
import os
import tarfile
import requests
from pathlib import Path
from random import randint

matieres = [
                "EnseignementScientifique", "Anglais", "Espagnol", "Mathematiques",
                "HistoireGeographie", "Physique", "EPS", "Philosophie", "Option"
            ]
matieres_map = {name: i for i, name in enumerate(matieres)}

def style_planning_text(val):
    """Applique une couleur de TEXTE différente selon la matière."""
    color = "#FAFAFA"
    weight = "normal"

    if val == "":
        color = "#555" 
    elif val == "Mathematiques" or val == "Physique" or val == "EnseignementScientifique":
        color = "#87CEFA"
        weight = "bold"
    elif val == "Anglais" or val == "Espagnol":
        color = "#90EE90"
    elif val == "HistoireGeographie" or val == "Philosophie":
        color = "#FFDAB9"
    elif val == "EPS" or val == "Option":
        color = "#D8BFD8"
    return f'color: {color}; font-weight: {weight};'

MINIZINC_VERSION = "2.9.4"
MINIZINC_INSTALL_DIR = Path("/tmp/minizinc_install")
archive_name = f"MiniZincIDE-{MINIZINC_VERSION}-bundle-linux-x86_64.tgz"
download_url = f"https://github.com/MiniZinc/MiniZincIDE/releases/download/{MINIZINC_VERSION}/{archive_name}"
MINIZINC_BUNDLE_DIR_NAME = f"MiniZincIDE-{MINIZINC_VERSION}-bundle-linux-x86_64"
MINIZINC_EXECUTABLE = MINIZINC_INSTALL_DIR / MINIZINC_BUNDLE_DIR_NAME / "bin" / "minizinc"

st.set_page_config(layout="wide")

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
                    for chunk in r.iter_content(chunk_size=8192*4):
                        f.write(chunk)
        with st.spinner(f"Extraction de MiniZinc {version}..."):
             with tarfile.open(archive_path, "r:gz") as tar:
                 tar.extractall(path=install_dir)
        if archive_path.exists(): archive_path.unlink()
        if executable_path.exists():
            subprocess.run(['chmod', '+x', str(executable_path)], check=True, timeout=5)
            st.sidebar.success(f"MiniZinc {version} installé.")
            return executable_path
        else:
            st.error(f"Exécutable MiniZinc introuvable après extraction: {executable_path}")
            return None
    except Exception as e:
        st.error(f"Échec de l'installation de MiniZinc: {e}")
        return None


minizinc_exe_path_obj = setup_minizinc(MINIZINC_VERSION, MINIZINC_INSTALL_DIR, MINIZINC_EXECUTABLE, archive_name, download_url)

if minizinc_exe_path_obj:
    try:
        driver = minizinc.Driver(minizinc_exe_path_obj)
        minizinc.default_driver = driver
        try:
             result = subprocess.run([str(minizinc_exe_path_obj), '--version'], capture_output=True, text=True, check=True, timeout=10)
        except Exception:
             st.sidebar.warning("Impossible de vérifier la version MiniZinc.")
    except Exception as e:
        st.error(f"Erreur config driver: {e}")
        st.stop()
else:
    st.error("Échec install MiniZinc.")
    st.stop()

solver = None
solver_tag_to_try = "cp-sat"
try:
    solver = minizinc.Solver.lookup(solver_tag_to_try)
except Exception as e:
    st.error(f"Solveur '{solver_tag_to_try}' introuvable ou erreur: {e}")
    st.stop()

st.title("Solveur d'Emploi du Temps 📅")

st.sidebar.header("Paramètres du Problème")

nombre_heures_jour_input = st.sidebar.number_input(
    "Nombre d'heures par jour",
    min_value=4,
    max_value=12,
    value=10,
    step=1
)

nombre_profs_input = st.sidebar.number_input(
    "Nombre de professeurs disponibles",
    min_value=5,
    max_value=50,
    value=11,
    step=1
)

num_classes_input = st.sidebar.number_input(
    "Nombre de classes",
    min_value=1,
    max_value=10,
    value=3,
    step=1
)

tailles_classes_input = []
default_capacites = [randint(25, 33) for _ in range(num_classes_input)]
st.sidebar.subheader("Capacité de chaque classe")
for i in range(num_classes_input):
    default_cap = default_capacites[i] if i < len(default_capacites) else 30
    size = st.sidebar.number_input(
        f"Taille Classe {i+1}",
        min_value=15,
        max_value=40,
        value=default_cap,
        step=1,
        key=f"taille_classe_{i}"
    )
    tailles_classes_input.append(size)

salles_enum_list = ["S101", "S102", "S201", "S202", "S203", "S204", "Gymnase", "Stade", "LaboPhysique1", "LaboPhysique2", "LaboChimie", "Empty"]
capacites_salles_input = []
st.sidebar.subheader("Capacité des salles")
default_capacites = [35, 35, 31, 30, 32, 29, 60, 100, 32, 32, 34, 0]
for i, salle_name in enumerate(salles_enum_list):
    if salle_name == "Empty":
        capacites_salles_input.append(0)
        continue
    default_cap = default_capacites[i] if i < len(default_capacites) else 30
    cap = st.sidebar.number_input(
        f"Capacité {salle_name}",
        min_value=0,
        max_value=150,
        value=default_cap,
        step=1,
        key=f"capacite_salle_{salle_name}"
    )
    capacites_salles_input.append(cap)

st.sidebar.subheader("Indisponibilité des professeurs (par demi-journée)")
demi_journees_options = {
    0: "Disponible",
    1: "Lundi Matin", 2: "Lundi Après-midi",
    3: "Mardi Matin", 4: "Mardi Après-midi",
    5: "Mercredi Matin", # 6 (Mercredi AM) est implicitement interdit
    7: "Jeudi Matin", 8: "Jeudi Après-midi",
    9: "Vendredi Matin", 10: "Vendredi Après-midi",
}
interdictions_input = []
for i in range(nombre_profs_input):
    selected_option = st.sidebar.selectbox(
        f"Prof P{i+1} indisponible le:",
        options=list(demi_journees_options.keys()),
        format_func=lambda x: demi_journees_options[x],
        key=f"interdiction_prof_{i}"
    )
    interdictions_input.append(selected_option)

st.sidebar.subheader("Affectations de certains professeurs à une matière spécifique")
affectations_input = []
for i in range(nombre_profs_input):
    selected_option = st.sidebar.selectbox(
        f"Prof P{i+1} affecté à :",
        options=list(matieres_map.keys()),
        format_func=lambda x: matieres_map[x],
        key=f"affectation_prof_{i}"
    )
    affectations_input.append(selected_option)

timeout_secondes = st.slider(
    "Temps de résolution maximum (secondes)",
    min_value=5, max_value=600, value=10, step=5
)

if st.button(f"Lancer la résolution ({num_classes_input} classes, max {timeout_secondes} sec)"):

    if solver is None:
        st.error("Config solveur échouée.")
        st.stop()

    try:
        model = minizinc.Model("./planning.mzn")
        inst = minizinc.Instance(solver, model)

        # Utilisation des valeurs des inputs
        inst["CLASS"] = range(1, num_classes_input + 1)
        inst["taille_classe"] = tailles_classes_input
        inst["PROFS"] = range(1, nombre_profs_input + 1)
        inst["nombre_heures_jour"] = nombre_heures_jour_input
        inst["DAY"] = range(1, nombre_heures_jour_input + 1)
        inst["WEEK"] = range(1, 5 + 1)
        inst["capacite_salle"] = capacites_salles_input
        inst["interdictions"] = interdictions_input
        inst["affectations"] = affectations_input

    except Exception as e:
        st.error(f"Erreur lors de la création de l'instance MiniZinc: {e}")
        st.stop()

    st.header("Résultat de la résolution")

    with st.spinner(f"Calcul en cours... ({num_classes_input} classes, limité à {timeout_secondes}s)"):
        result = None
        try:
            try:
                import ortools
                ortools_package_dir = Path(ortools.__file__).parent
                lib_paths_to_check = [ortools_package_dir, ortools_package_dir / ".libs"]
                found_lib_paths = [str(p) for p in lib_paths_to_check if p.is_dir()]
                if found_lib_paths:
                    current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
                    new_ld_path = ":".join(found_lib_paths)
                    if current_ld_path: new_ld_path = new_ld_path + ":" + current_ld_path
                    os.environ['LD_LIBRARY_PATH'] = new_ld_path
            except Exception: pass

            result = inst.solve(
                processes=8,
                timeout=datetime.timedelta(seconds=timeout_secondes)
            )

        except Exception as e:
            st.error(f"Une erreur est survenue pendant la résolution : {e}")
            st.exception(e)
            st.stop()

    if result and result.solution:
        status_message = f"Statut: {result.status}"
        if result.status == minizinc.Status.OPTIMAL_SOLUTION:
            st.success(f"🎉 Solution Optimale trouvée ! ({status_message})")
        elif result.status == minizinc.Status.SATISFIED:
            st.warning(f"⚠️ Timeout atteint ! Meilleure solution trouvée. ({status_message})")
        else:
            st.info(f"Recherche terminée. ({status_message})")

        st.info(f"Score de l'objectif = {result.objective}")
        solution = result.solution

        jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
        nombre_heures = 0
        heures = []

        if hasattr(solution, "planning"):
            def style_cell_html(cell_value):
                """Génère une balise span HTML avec style basé sur la matière."""
                if not cell_value or cell_value == "":
                    return '<span style="color: #555;"></span>' # Gris pour Void/vide

                lines = cell_value.split('\n')
                matiere = lines[0]
                
                color = "#FAFAFA" # Blanc cassé par défaut
                weight = "normal"
                if matiere == "Mathematiques" or matiere == "Physique" or matiere == "EnseignementScientifique":
                    color = "#87CEFA" # Bleu ciel
                    weight = "bold"
                elif matiere == "Anglais" or matiere == "Espagnol":
                    color = "#90EE90" # Vert clair
                elif matiere == "HistoireGeographie" or matiere == "Philosophie":
                    color = "#FFDAB9" # Pêche
                elif matiere == "EPS" or matiere == "Option":
                    color = "#D8BFD8" # Violet clair
                html_content = cell_value.replace('\n', '<br>')

                return f'<span style="color: {color}; font-weight: {weight};">{html_content}</span>'


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
                            if c<len(planning_data) and planning_data[c] is not None and \
                               d<len(planning_data[c]) and planning_data[c][d] is not None and \
                               w<len(planning_data[c][d]):

                                matiere_obj = planning_data[c][d][w]
                                if matiere_obj is not None :
                                     matiere_name = str(matiere_obj)
                                     if matiere_name != "Void":
                                         salle_name = ""
                                         prof_name = ""

                                         if planning_salle_data and c < len(planning_salle_data) and \
                                            d < len(planning_salle_data[c]) and w < len(planning_salle_data[c][d]):
                                             salle_obj = planning_salle_data[c][d][w]
                                             if salle_obj is not None and str(salle_obj) != "Empty":
                                                 salle_name = str(salle_obj)

                                         if prof_to_class_data and prefs_data and matiere_name in matieres_map:
                                             matiere_index = matieres_map[matiere_name]
                                             for p_index in profs_indices:
                                                 if p_index < len(prof_to_class_data) and c < len(prof_to_class_data[p_index]) and \
                                                    prof_to_class_data[p_index][c] == 1 and \
                                                    p_index < len(prefs_data) and matiere_index < len(prefs_data[p_index]) and \
                                                    prefs_data[p_index][matiere_index] == 1:
                                                     prof_name = f"P{p_index+1}"
                                                     break
                                         
                                         cell_text_raw = matiere_name
                                         if prof_name: cell_text_raw += f"\n({prof_name})"
                                         if salle_name: cell_text_raw += f"\n[{salle_name}]"
                            planning_display_list[d][w] = style_cell_html(cell_text_raw)


                    df = pd.DataFrame(planning_display_list, columns=jours, index=heures)
                    st.markdown(df.to_html(escape=False, index=True), unsafe_allow_html=True)

            else:
                 st.warning("Données de planning vides ou invalides.")
        else:
            st.warning("Variable 'planning' non trouvée dans la solution.")

        if not heures:
             try:
                 nombre_heures_mzn = inst["nombre_heures_jour"]
                 if nombre_heures_mzn > 0:
                      nombre_heures = nombre_heures_mzn
                      heures = [f"H{d} ({d+7}h)" for d in range(1, nombre_heures + 1)]
                 else: st.error("Impossible de déterminer le nombre d'heures."); st.stop()
             except KeyError: st.error("'nombre_heures_jour' non trouvé."); st.stop()


        if (hasattr(solution, "prof_est_utilise") and
            hasattr(solution, "prefs") and
            hasattr(solution, "planning_prof") and
            hasattr(solution, "planning") and hasattr(solution, "planning") and 'planning_data' in locals() # Check if planning_data was defined
             and hasattr(solution, "prof_to_class")):

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
                    # Ensure inner list exists and has enough elements
                    if prefs_data[p_index] is not None and len(prefs_data[p_index]) > len(matieres):
                        for i in range(len(matieres)):
                            if prefs_data[p_index][i] == 1:
                                competences.append(matieres[i])
                if not competences: competences = ["(Aucune)"]
                prefs_display.append(f"Prof P{p_index+1} : {', '.join(competences)}")

            st.subheader("Compétences des professeurs recrutés :")
            st.text("\n".join(prefs_display))

            st.subheader("Plannings des professeurs :")
            for p_index in profs_indices:
                st.write(f"**Prof P{p_index+1}**")
                prof_schedule_display = [["" for _ in jours] for _ in range(nombre_heures)]

                for d in range(nombre_heures):
                    for w in range(len(jours)):
                        for c in range(num_classes_sol):
                            # Add more robust bound checks
                            if c < len(planning_data) and planning_data[c] is not None and \
                               d < len(planning_data[c]) and planning_data[c][d] is not None and \
                               w < len(planning_data[c][d]):
                                matiere_obj = planning_data[c][d][w]
                                if matiere_obj is not None:
                                    if p_index < len(prof_to_class_data) and prof_to_class_data[p_index] is not None and \
                                       c < len(prof_to_class_data[p_index]):
                                        is_assigned = (prof_to_class_data[p_index][c] == 1)
                                        if not is_assigned: continue

                                    matiere_name = str(matiere_obj)
                                    if matiere_name in matieres_map:
                                        matiere_index = matieres_map[matiere_name]
                                        if p_index < len(prefs_data) and prefs_data[p_index] is not None and \
                                           matiere_index < len(prefs_data[p_index]):
                                            is_competent = (prefs_data[p_index][matiere_index] == 1)
                                            if is_competent:
                                                prof_schedule_display[d][w] = f"Classe {c+1}"
                                                break

                df = pd.DataFrame(prof_schedule_display, columns=jours, index=heures)
                styled_df = df.style.map(style_planning_text)
                config = {jour: st.column_config.TextColumn(width="medium") for jour in jours}
                st.dataframe(styled_df, column_config=config, width="stretch")
        else:
            st.warning("Variables professeurs non trouvées ou incomplètes pour afficher les plannings.")

        if hasattr(solution, "planning_salle"):
            st.header("Occupation des Salles")
            salles_list_display = [s for s in salles_enum_list if s != "Empty"]
            room_schedules = {salle: [["" for _ in jours] for _ in range(nombre_heures)] for salle in salles_list_display}
            planning_salle_data = solution.planning_salle
            num_classes_sol = len(planning_salle_data)
            num_jours = len(jours)

            for c in range(num_classes_sol):
                for d in range(nombre_heures):
                    for w in range(num_jours):
                         if c < len(planning_salle_data) and planning_salle_data[c] is not None and \
                            d < len(planning_salle_data[c]) and planning_salle_data[c][d] is not None and \
                            w < len(planning_salle_data[c][d]):
                            salle_obj = planning_salle_data[c][d][w]
                            if salle_obj is not None:
                                salle_name = str(salle_obj)
                                if salle_name != "Empty" and salle_name in room_schedules:
                                    room_schedules[salle_name][d][w] = f"Classe {c+1}"

            for salle_name, schedule_data in room_schedules.items():
                st.subheader(f"Salle: {salle_name}")
                df = pd.DataFrame(schedule_data, columns=jours, index=heures)
                styled_df = df.style.map(style_planning_text)
                config = {jour: st.column_config.TextColumn(width="medium") for jour in jours}
                st.dataframe(styled_df, column_config=config, width="stretch")
        else:
            st.warning("Variable 'planning_salle' non trouvée.")

    elif result and result.status == minizinc.Status.UNSATISFIABLE:
        st.error(f"Le modèle est UNSAT (Insoluble) avec ces paramètres. Statut: {result.status}")
    elif result:
        st.error(f"Le solveur n'a retourné aucune solution (Statut: {result.status}).")
    else:
        st.error("La résolution a échoué sans retourner de statut.")