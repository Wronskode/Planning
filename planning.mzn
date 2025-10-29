enum MATIERES = {EnseignementScientifique, Anglais, Espagnol, Mathematiques, HistoireGeographie, Physique, EPS, Philosophie, Option, Void};
set of int: PROFS;
int: nombre_heures_jour;
set of int: DAY;
set of int: WEEK;
set of int: CLASS;
array[PROFS] of int: interdictions;
% Le nombre d'élèves par classe
array[CLASS] of int: taille_classe;
% L'ensemble des salles
enum SALLES = {S101, S102, S201, S202, S203, S204, Gymnase, Stade, LaboPhysique1, LaboPhysique2, LaboChimie, Empty};
array[PROFS] of MATIERES: affectations;
% La capacité de chaque salle
array[SALLES] of int: capacite_salle;
% array[SALLES] of var 0..: capacite_salle;
   % S101, S102, S201, S202, S203, S204,      Gymnase, Stade, LaboPhysique, LaboChimie, Empty

array[MATIERES] of set of SALLES: salles_compatibles = [
    {S101, S102, S201, S202, S203, S204},                 % EnseignementScientifique
    {S101, S102, S201, S202, S203, S204},                 % Anglais
    {S101, S102, S201, S202, S203, S204},                 % Espagnol
    {S101, S102, S201, S202, S203, S204},                 % Mathematiques
    {S101, S102, S201, S202, S204},                 % HistoireGeographie
    {LaboPhysique1, LaboPhysique2, LaboChimie},                           % Physique
    {Gymnase, Stade},                                % EPS
    {S101, S102, S201, S202, S203, S204},                 % Philosophie
    {S101, S102, S201, S202, S203, S204},                 % Option
    SALLES                                   % Void (peut être n'importe où)
];
array[PROFS, MATIERES] of var 0..1: prefs;
array [PROFS, CLASS] of var 0..1: prof_to_class;
array[CLASS, DAY, WEEK] of var MATIERES: planning;
array[PROFS, DAY, WEEK] of var 0..1: planning_prof; % 0 = libre, 1 = occupé


array[CLASS, DAY, WEEK] of var SALLES: planning_salle;
% Quotas d'heures par matière
constraint forall(c in CLASS) (sum(d in DAY, w in WEEK) (bool2int(planning[c, d, w] = EnseignementScientifique)) = 2);
constraint forall(c in CLASS) (sum(d in DAY, w in WEEK) (bool2int(planning[c, d, w] = Anglais)) = 2);
constraint forall(c in CLASS) (sum(d in DAY, w in WEEK) (bool2int(planning[c, d, w] = Mathematiques)) = 6);
constraint forall(c in CLASS) (sum(d in DAY, w in WEEK) (bool2int(planning[c, d, w] = Physique)) = 6);
constraint forall(c in CLASS) (sum(d in DAY, w in WEEK) (bool2int(planning[c, d, w] = Espagnol)) = 2);
constraint forall(c in CLASS) (sum(d in DAY, w in WEEK) (bool2int(planning[c, d, w] = EPS)) = 2);
constraint forall(c in CLASS) (sum(d in DAY, w in WEEK) (bool2int(planning[c, d, w] = Philosophie)) = 3);
constraint forall(c in CLASS) (sum(d in DAY, w in WEEK) (bool2int(planning[c, d, w] = HistoireGeographie)) = 2);
constraint forall(c in CLASS) (sum(d in DAY, w in WEEK) (bool2int(planning[c, d, w] = Option)) = 3);

% Contraintes horaires (classes)
constraint forall (c in CLASS) (forall(w in WEEK where w != 3) (planning[c, 4, w] = planning[c, 5, w] /\ planning[c, 5, w] = Void \/ planning[c, 5, w] = planning[c, 6, w] /\ planning[c, 5, w] = Void));
constraint forall (c in CLASS) (forall(d in DAY where d > 4) (planning[c, d, 3] = Void)); % Mercredi après-midi

% Contraintes pédagogiques
constraint forall(c in CLASS) (forall(m in MATIERES where m != Void) (forall(w in WEEK) (sum(d in DAY) (bool2int(planning[c, d, w] = m)) <= 3)));
constraint forall(c in CLASS) (exists(d in 1..(nombre_heures_jour-1), w in WEEK) (planning[c, d, w] = HistoireGeographie /\ planning[c, d+1, w] = HistoireGeographie));
constraint forall(c in CLASS) (exists(d in 1..(nombre_heures_jour-1), w in WEEK) (planning[c, d, w] = Philosophie /\ planning[c, d+1, w] = Philosophie));
constraint forall(c in CLASS) (forall(w in WEEK) (sum(d in DAY) (bool2int(planning[c, d, w] = Philosophie)) <= 2));
constraint forall(c in CLASS) (forall(w in WEEK)
    (planning[c, 1, w] = HistoireGeographie -> planning[c, 2, w] = HistoireGeographie));
    
constraint forall(c in CLASS, w in WEEK, d in DAY) (
    % SI c'est des Maths
    (planning[c, d, w] = Mathematiques) ->
    (
        % ALORS le précédent OU le suivant doit aussi être Maths
        (d > 1 /\ planning[c, d-1, w] = Mathematiques)
        \/
        (d < nombre_heures_jour /\ planning[c, d+1, w] = Mathematiques)
    )
);    

constraint forall(c in CLASS, w in WEEK, d in DAY) (
    (planning[c, d, w] = Physique) ->
    (
        (d > 1 /\ planning[c, d-1, w] = Physique)
        \/
        (d < nombre_heures_jour /\ planning[c, d+1, w] = Physique)
    )
);    

constraint forall(c in CLASS, w in WEEK, d in DAY) (
    (planning[c, d, w] = EnseignementScientifique) ->
    (
        (d > 1 /\ planning[c, d-1, w] = EnseignementScientifique)
        \/
        (d < nombre_heures_jour /\ planning[c, d+1, w] = EnseignementScientifique)
    )
);

constraint forall(c in CLASS, w in WEEK, d in DAY) (planning[c, d, w] = Espagnol -> forall(d2 in DAY where d != d2) (planning[c, d2, w] != Espagnol));
constraint forall(c in CLASS, w in WEEK, d in DAY) (planning[c, d, w] = Anglais -> forall(d2 in DAY where d != d2) (planning[c, d2, w] != Anglais));
constraint forall(c in CLASS) (exists(w in WEEK) (forall (d in 1..2) (planning[c, d, w] = EPS)));

constraint forall (p in PROFS) (sum(m in MATIERES) (prefs[p, m] = 1) <= 1);
% --- Gestion des ressources (Professeurs) ---
constraint forall(p in PROFS, d in DAY, w in WEEK) (
    planning_prof[p, d, w] = 
        sum(c in CLASS) (
            bool2int(
                prof_to_class[p, c] = 1 /\ 
                element(enum2int(planning[c, d, w]), prefs[p, ..]) = 1
            )
        )
);

% Contraintes horaires (profs)
constraint forall(p in PROFS) (sum(d in DAY, w in WEEK) (planning_prof[p, d, w]) <= 24);
constraint forall (p in PROFS) (forall(d in DAY where d > 4) (planning_prof[p, d, 3] = 0)); % Mercredi AM
constraint forall (p in PROFS) (forall(w in WEEK where w != 3) (planning_prof[p, 4, w] = planning_prof[p, 5, w] /\ planning_prof[p, 5, w] = 0 \/ planning_prof[p, 5, w] = planning_prof[p, 6, w] /\ planning_prof[p, 5, w] = 0));


constraint forall(c in CLASS, d in DAY, w in WEEK) (
    planning[c, d, w] != Void -> 
        element(enum2int(planning_salle[c, d, w]), capacite_salle) >= taille_classe[c]
);

constraint forall(c in CLASS, d in DAY, w in WEEK) (
    planning[c, d, w] != Void -> 
        planning_salle[c, d, w] in salles_compatibles[planning[c, d, w]]
);


constraint forall(s in SALLES where s != Empty, d in DAY, w in WEEK) (
    sum(c in CLASS) (
        bool2int(planning_salle[c, d, w] = s)
    ) <= 1
);

constraint forall(c in CLASS, d in DAY, w in WEEK) (
    planning[c, d, w] = Void <-> planning_salle[c, d, w] = Empty
);

constraint forall(c in CLASS, w in WEEK, d in 1..(nombre_heures_jour - 1)) (
    (planning[c, d, w] = planning[c, d+1, w])
    ->
    (planning_salle[c, d, w] = planning_salle[c, d+1, w])
);

constraint forall(c in CLASS, d in DAY, w in WEEK where planning[c, d, w] != Void) (
    sum(p in PROFS) (
         bool2int(
              prof_to_class[p, c] = 1
              /\
              element(enum2int(planning[c, d, w]), prefs[p, ..]) = 1
              /\
              planning_prof[p, d, w] = 1 
         )
    ) = 1
);
% Interdictions profs horaires

constraint forall (p in PROFS) (interdictions[p] = 1 -> forall(d in 1..4) (planning_prof[p, d, 1] = 0));
constraint forall (p in PROFS) (interdictions[p] = 2 -> forall(d in 5..nombre_heures_jour) (planning_prof[p, d, 1] = 0));
constraint forall (p in PROFS) (interdictions[p] = 3 -> forall(d in 1..4) (planning_prof[p, d, 2] = 0));
constraint forall (p in PROFS) (interdictions[p] = 4 -> forall(d in 5..nombre_heures_jour) (planning_prof[p, d, 2] = 0));
constraint forall (p in PROFS) (interdictions[p] = 5 -> forall(d in 1..4) (planning_prof[p, d, 3] = 0));
constraint forall (p in PROFS) (interdictions[p] = 6 -> forall(d in 5..nombre_heures_jour) (planning_prof[p, d, 3] = 0));
constraint forall (p in PROFS) (interdictions[p] = 7 -> forall(d in 1..4) (planning_prof[p, d, 4] = 0));
constraint forall (p in PROFS) (interdictions[p] = 8 -> forall(d in 5..nombre_heures_jour) (planning_prof[p, d, 4] = 0));
constraint forall (p in PROFS) (interdictions[p] = 9 -> forall(d in 1..4) (planning_prof[p, d, 5] = 0));
constraint forall (p in PROFS) (interdictions[p] = 10 -> forall(d in 5..nombre_heures_jour) (planning_prof[p, d, 5] = 0));

% Affectations
constraint forall (p in PROFS) (affectations[p] != Void -> prefs[p, affectations[p]] = 1);
% --- Définition des composantes de l'objectif ---
var int: obj_trous_compacts = 
    sum(c in CLASS, w in WEEK, d in 2..(nombre_heures_jour - 1)) (
        bool2int(planning[c, d, w] = Void /\ planning[c, d+1, w] != Void)
    );

var int: obj_equilibrage_profs = max(p in PROFS) (
    sum(d in DAY, w in WEEK) (planning_prof[p, d, w])
);

array[PROFS] of var 0..1: prof_est_utilise;

constraint forall(p in PROFS) (
    prof_est_utilise[p] = 1 <-> sum(c in CLASS) (prof_to_class[p, c]) > 0
);

constraint forall(p in PROFS) (
    prof_est_utilise[p] = 1 -> sum(d in DAY, w in WEEK) (planning_prof[p, d, w]) >= 1
);

constraint forall(p in 1..(card(PROFS) - 1)) (
    prof_est_utilise[p] >= prof_est_utilise[p+1]
);

var int: obj_prof_used = sum(p in PROFS) (prof_est_utilise[p]);
var int: obj_eps_late = sum (c in CLASS, d in DAY, w in WEEK) (
    bool2int(planning[c, d, w] = EPS /\ w <= 3)
);
    
var int: obj_makespan = max(w in WEEK, d in DAY, c in CLASS) ( 
    bool2int(planning[c, d, w] != Void) * ((w-1)*nombre_heures_jour + d)
);

var int: obj_trous_profs = 
    sum(p in PROFS, w in WEEK, d in 1..(nombre_heures_jour - 1)) (
        bool2int(planning_prof[p, d, w] = 0 /\ planning_prof[p, d+1, w] = 1)
    );
    
var int: count_start_after_8am = 
    sum(c in CLASS, w in WEEK) (
        bool2int(planning[c, 1, w] = Void)
    );    
% --- Objectif final pondéré ---
var int: obj = 
      (100000 * obj_prof_used)           % Prio 1: Minimiser le nb de profs
    + (10000 * obj_trous_compacts)        % Prio 2: Pas de trous pour les élèves
    - (5000 * count_start_after_8am)
    + (1000 * obj_trous_profs)          % Prio 3: Pas de trous pour les profs
    + (100 * obj_equilibrage_profs)     % Prio 4: Équilibrer la charge max
    + (10 * obj_eps_late)               % Prio 5: EPS l'après-midi
    + (2500 * obj_makespan);               % Prio 6: Finir tôt
% var int: obj = obj_prof_used;
solve minimize obj;
    
output
       [ "Classe \(c):\n" ++ show2d(planning[c, .., ..]) ++ "\n"
         | c in CLASS
       ]
       ++
       [ "Prof P\(p):\n" ++ show2d(planning_prof[p, .., ..]) ++ "\n"
         | p in PROFS
       ]++
       [ "Prof p to class c :\n" ++ show2d(prof_to_class[..,..]) ++ "\n"]
       ++ [ "Salles pour la classe \(c) :\n" ++ show2d(planning_salle[c,..,..]) ++ "\n" | c in CLASS]
       ++ ["Profs :\n" ++ show2d(prefs[..,..]) ++ "\n"]
       ++["Nombre professeurs utilisés : \(obj_prof_used)\n" ]
       ++["Objectif : \(obj)\n\n"];