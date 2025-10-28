# 📅 Solveur d'Emplois du Temps Scolaire - Un projet de Recherche Opérationnelle

Bonjour ! Je suis Julien, étudiant en M2 Algorithmique à l'Université de Montpellier, passionné par la résolution de problèmes complexes grâce à l'informatique et aux mathématiques. Ce projet est une exploration personnelle dans le domaine de la Recherche Opérationnelle (R.O.), appliquée au casse-tête bien connu de la création d'emplois du temps scolaires.

L'objectif ? Aller au-delà d'un simple planning et créer un outil capable de jongler avec une multitude de contraintes réelles (pédagogiques, logistiques, humaines) et même d'optimiser le recrutement des professeurs nécessaires !

# 🚀 Découvrez l'application en direct ici : [Lien vers ton application Streamlit Cloud]
(Note : Le solveur travaille dur ! La résolution peut prendre quelques minutes, surtout si vous augmentez le nombre de classes.)

(Insère ici une capture d'écran sympa de ton application Streamlit)

# 🎯 Le Défi : Plus qu'un simple planning

Créer un emploi du temps scolaire, c'est un peu comme jouer à Tetris en 4 dimensions avec des règles qui changent tout le temps. Il faut affecter des cours à des créneaux horaires, mais aussi :

Respecter les quotas d'heures pour chaque matière.

Gérer les ressources limitées : professeurs (avec leurs compétences spécifiques) et salles (avec leurs capacités et équipements).

Prendre en compte des contraintes pédagogiques : cours en blocs (pas d'heure isolée de Maths !), pauses obligatoires (mercredi après-midi, déjeuner), cours spécifiques le matin, etc.

Éviter les conflits : un prof ou une salle ne peuvent pas être à deux endroits en même temps.

Et si possible... optimiser pour le confort de tous (éviter les "trous" dans les journées) et l'efficacité (utiliser le moins de professeurs possible).

Ce projet tente de relever ce défi en utilisant la Programmation Par Contraintes (PPC).

# 🛠️ L'Approche Technique : La puissance de la PPC

J'ai choisi la PPC car elle excelle dans la gestion de problèmes combinatoires complexes avec des règles logiques hétérogènes.

Modélisation : Le cœur du projet est un modèle écrit en MiniZinc, un langage déclaratif puissant pour décrire des problèmes sous contraintes.

Résolution : J'utilise Google OR-Tools CP-SAT comme solveur principal (via l'intégration MiniZinc). C'est un solveur SAT/CP open-source extrêmement performant, surtout pour les problèmes de planification. (Note pour l'application cloud : en raison de défis de configuration spécifiques à l'environnement d'hébergement, l'application déployée utilise Gecode, un autre solveur CP robuste, comme alternative).

Interface & Pilotage : Une application web interactive développée en Python avec Streamlit permet de paramétrer le problème et de visualiser les résultats. La communication avec MiniZinc se fait via la bibliothèque minizinc-python, et les plannings sont joliment affichés grâce à Pandas.

# 🧩 Au cœur du modèle MiniZinc

Le modèle MiniZinc est le cerveau de l'opération. Voici les éléments clés :

Variables de Décision Principales :

planning[Classe, Jour, Semaine]: Quelle matière a lieu ?

planning_salle[Classe, Jour, Semaine]: Dans quelle salle ?

prefs[Prof, Matiere]: Quelles sont les compétences de chaque prof ? (Mode avancé : cette matrice est une variable, le solveur décide des compétences !)

prof_to_class[Prof, Classe]: Quel prof est assigné à quelle classe ?

planning_prof[Prof, Jour, Semaine]: Le prof est-il occupé ?

Contraintes Majeures Implémentées :

Respect des quotas horaires par matière.

Gestion des conflits : un prof/une salle à la fois.

Contraintes de capacité des salles vs taille des classes.

Compatibilité salle/matière (ex: Physique en labo, EPS au gymnase).

Pauses (déjeuner, mercredi après-midi).

Cours en blocs/contigus pour certaines matières (Maths, Physique, HG...).

Placement spécifique (ex: EPS le matin).

(Mode avancé) Limitation du nombre de matières par professeur.

(Mode avancé) Bris de symétrie pour optimiser la recherche du nombre minimal de professeurs.

Fonction Objectif Pondérée (Multi-critères) : Parce qu'un "bon" emploi du temps, c'est subjectif, l'objectif combine plusieurs critères avec des priorités (style lexicographique) :

(Priorité Max) Minimiser le nombre de professeurs recrutés.

Minimiser les "trous" dans les journées des élèves.

Minimiser les "trous" dans les journées des professeurs.

Équilibrer la charge de travail maximale entre les professeurs.

Préférence pour placer l'EPS l'après-midi/fin de semaine.

Minimiser le "makespan" (finir les cours le plus tôt possible, en dernier recours).

# ✨ Fonctionnalités de l'Application Web

L'interface Streamlit vous permet de :

Choisir le nombre de classes.

Définir la taille de chaque classe.

Ajuster le nombre total de professeurs disponibles dans le "pool de recrutement".

Modifier la capacité de chaque salle.

Définir un temps limite pour la résolution (important pour les instances complexes !).

Visualiser les résultats :

Plannings détaillés par classe.

Liste des professeurs recrutés et leurs compétences (décidées par le solveur !).

Plannings individuels des professeurs (montrant les classes assignées).

Planning d'occupation pour chaque salle.

# 🚀 Comment l'utiliser ?

En ligne : Cliquez simplement sur le lien Streamlit Cloud en haut de ce README ! Jouez avec les paramètres dans la barre latérale et cliquez sur "Lancer la résolution".

En local :

Clonez ce dépôt : git clone https://github.com/Wronskode/Planning.git

Installez les dépendances : pip install -r requirements.txt

(Assurez-vous d'avoir MiniZinc installé sur votre système et accessible dans le PATH si vous n'utilisez pas la version packagée ortools)

Lancez l'application : streamlit run app.py

# 🤔 Défis Rencontrés & Points Techniques

Ce projet a été un excellent terrain d'apprentissage, notamment sur :

La complexité du mode prefs en var : Laisser le solveur choisir les compétences des profs augmente énormément l'espace de recherche. L'ajout de contraintes de bris de symétrie (prof_est_utilise) a été crucial pour guider le solveur.

Déploiement sur Streamlit Cloud : Configurer l'environnement pour que Python, MiniZinc (téléchargé manuellement), et CP-SAT (via ortools) communiquent correctement a nécessité des ajustements spécifiques (variables d'environnement LD_LIBRARY_PATH, gestion des dépendances système via packages.txt).

Gestion des versions : Des différences subtiles entre les versions de MiniZinc et minizinc-python (ex: existence de enum2int, nom des exceptions) ont demandé des adaptations pour assurer la compatibilité.

# 🚧 Limitations et Pistes d'Amélioration

Ce solveur est un prototype, et il y a plein de pistes pour aller plus loin :

Performance : Pour des instances plus grandes (beaucoup de classes/profs), le temps de calcul peut devenir important, surtout avec prefs en var. Revenir à un prefs fixe (par) accélérerait grandement la résolution pour une utilisation "classique".

Contraintes supplémentaires : On pourrait ajouter des contraintes plus fines (ex: pauses spécifiques pour les profs, alternance de matières, préférences prof/classe...).

Objectif plus riche : Intégrer des coûts (salaire profs), des préférences plus détaillées.

Interface : Permettre l'édition manuelle des plannings, visualiser les "points de blocage" quand le modèle est UNSAT.

Tests : Mettre en place des tests de performance plus formels sur des benchmarks standards.

N'hésitez pas à explorer le code et à lancer l'application. Ce projet m'a beaucoup appris sur la puissance de la R.O. et de la PPC pour résoudre des problèmes concrets et complexes !

Julien