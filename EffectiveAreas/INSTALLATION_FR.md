# Environnement RNO-G sans Anaconda

Cette procédure prépare un environnement dédié à la génération de neutrinos,
à la simulation radio et au calcul des aires effectives. Elle fournit les
commandes à exécuter toi-même : aucune installation n'a été effectuée ici.

## Choix adaptés à ton Mac

Vérification après mise à jour : macOS 27.2.1, un processeur ARM64, un ancien
Homebrew dans `/usr/local/bin`, et aucun Homebrew dans `/opt/homebrew`.
Xcode est sélectionné, mais son SDK macOS est encore en version 14.2.
Nous allons utiliser des outils de compilation à jour et une installation
native ARM64 pour ce projet.

La configuration proposée est Python 3.11, un environnement `.venv`, et
NuRadioMC au tag `v3.1.0`. Ce tag constitue un point de départ reproductible ;
le choix du code de production pourra ensuite être aligné sur celui recommandé
par la collaboration. NumPy 1.26.4 est un choix conservateur pour commencer avec
cette version de NuRadioMC, pas une matrice de compatibilité officiellement
validée. Les tests ci-dessous servent à vérifier l'installation obtenue.

Homebrew installera Python et GSL. Le module standard `venv` créera l'environnement
Python isolé, puis `pip` installera les packages dans ce venv. GSL est une
bibliothèque C externe au venv. Anaconda et uv ne sont nécessaires à aucune
de ces étapes.

Répartition entre comptes : le compte administrateur propriétaire de Homebrew
effectue les étapes 1 à 3 et la commande `brew install` au début de l'étape 4.
Ensuite, le compte de travail `chiche` crée `.venv` dans son projet et effectue
toutes les installations avec pip, les compilations et les simulations.
Les commandes `brew` sont lancées par leur compte propriétaire, sans `sudo`.
Les programmes installés sont utilisables depuis `chiche` si leurs permissions
permettent la lecture et l'exécution, comme avec les permissions habituelles
de Homebrew. Voir la [FAQ Homebrew](https://docs.brew.sh/FAQ#what-are-the-default-ownership-and-permissions-used-by-homebrew).

La documentation NuRadioMC signale des difficultés avec PROPOSAL sous Anaconda
sur macOS. Cette procédure utilise donc un venv fondé sur Python Homebrew.

Sources : [installation NuRadioMC](https://nu-radio.github.io/NuRadioMC/Introduction/pages/installation.html),
[version v3.1.0](https://github.com/nu-radio/NuRadioMC/releases/tag/v3.1.0),
[Homebrew](https://docs.brew.sh/Installation),
[venv](https://docs.python.org/3.11/library/venv.html).

## 1. Partir d'un terminal natif et quitter Conda

Dans le terminal :

```bash
uname -m
```

Le résultat attendu est `arm64`. Si le terminal affiche `x86_64`, ouvre une
session native ARM64 avant de continuer.

Si un environnement Conda est actif, exécute :

```bash
conda deactivate
```

Répète si nécessaire jusqu'à quitter tous les niveaux Conda actifs. Cela
désactive l'environnement dans ce terminal ; cela ne désinstalle rien.

## 2. Mettre à jour les outils de compilation Apple

```bash
xcode-select -p
clang --version
xcrun --show-sdk-version
make --version
```

Ils permettent de compiler le ray tracer et, si nécessaire, PROPOSAL. Le SDK
14.2 actuellement sélectionné provient de l'ancienne installation ; mets à jour
Xcode ou les Command Line Tools avant les compilations.

Tu peux demander l'installation des outils avec :

```bash
xcode-select --install
```

Si macOS indique qu'ils sont déjà installés, recherche leur mise à jour dans
Réglages Système > Général > Mise à jour de logiciels, ou mets à jour Xcode.
Après installation des Command Line Tools récents, si Xcode reste sélectionné
avec son ancien SDK, tu peux sélectionner les nouveaux outils :

```bash
sudo xcode-select --switch /Library/Developer/CommandLineTools
xcrun --show-sdk-version
```

Cette sélection est à faire uniquement si les outils viennent bien d'être
installés ou mis à jour à cet emplacement. Si tu as mis à jour Xcode lui-même,
tu peux conserver Xcode sélectionné et vérifier son nouveau SDK.

## 3. Installer Homebrew natif ARM64

Le préfixe standard Apple Silicon est `/opt/homebrew`. Utilise l'
[installateur officiel](https://brew.sh/), exécuté en ARM64 :

```bash
arch -arm64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Charge ce Homebrew dans le terminal courant et vérifie son emplacement :

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
/opt/homebrew/bin/brew --prefix
```

Le résultat attendu est `/opt/homebrew`. Cet outil installe les logiciels et
bibliothèques externes à Python. Suis aussi les instructions de fin d'installation
si tu souhaites rendre sa configuration persistante dans les nouveaux terminaux.

## 4. Installer Python et GSL, puis créer le venv

Sur le compte administrateur propriétaire de Homebrew :

```bash
/opt/homebrew/bin/brew install python@3.11 gsl
```

Reviens ensuite sur ton compte de travail `chiche`. Dans son terminal :

```bash
cd /Users/chiche/Desktop/GRBsRNO
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
```

Homebrew installe Python 3.11 et la bibliothèque numérique GSL. La commande
`python3.11 -m venv` crée un environnement isolé dans `.venv` avec `pip`.
`source` active cet environnement pour les commandes suivantes. Le chemin explicite
vers Python évite de sélectionner l'ancienne installation Intel.

Vérifie l'interpréteur :

```bash
python -c 'import sys, platform; print(sys.executable); print(platform.machine()); print(sys.prefix != sys.base_prefix)'
python -m pip --version
```

Résultats attendus : un exécutable dans `GRBsRNO/.venv/bin/python`, `arm64`,
puis `True`. pip doit lui aussi provenir de `.venv`.

Sources : [Python 3.11 Homebrew](https://formulae.brew.sh/formula/python@3.11),
[environnements venv](https://docs.python.org/3.11/library/venv.html).

## 5. Installer les outils Python de compilation

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install "numpy==1.26.4" six cython "cmake>=3.23,<4" "conan>=2,<3"
```

NumPy fournit les tableaux numériques. Cython compile l'interface Python du
ray tracer. CMake et Conan servent à construire les bibliothèques C++ utilisées
par PROPOSAL. La borne sur CMake conserve ici une version 3 pour ce logiciel
plus ancien.

`six` est utilisé par le générateur et les utilitaires Veff de NuRadioMC 3.1.0,
mais cette version ne le déclare pas dans ses dépendances. Il faut donc
l'installer explicitement. `pip check` ne détecte pas cet oubli de déclaration.

Utilise `python -m pip` : cela relie explicitement l'installation de packages au
Python que tu viens de vérifier.

## 6. Installer NuRadioMC et les bibliothèques scientifiques

```bash
mkdir -p .software
git clone --branch v3.1.0 --depth 1 https://github.com/nu-radio/NuRadioMC.git .software/NuRadioMC
python -m pip install "numpy==1.26.4" -e .software/NuRadioMC
python -m pip install "numpy==1.26.4" pandas ipykernel
```

`-e` réalise une installation éditable : Python utilise le code du dépôt cloné.
Cela facilite la lecture des exemples et la compilation du ray tracer dans un
dossier accessible en écriture. Garde ce dossier en place.

NuRadioMC déclare et installe ses dépendances principales, dont NuRadioReco,
SciPy, Matplotlib, Astropy, h5py, radiotools et PyYAML. Il n'est pas nécessaire
d'installer NuRadioReco séparément.

| Composant | Utilité |
| --- | --- |
| NuRadioMC | Génération des interactions, émission radio et propagation. |
| NuRadioReco | Réponse du détecteur, traitement des signaux et triggers. |
| NumPy / SciPy | Calcul numérique, intégration et interpolation. |
| Matplotlib | Figures et courbes d'aires effectives. |
| h5py | Lecture et écriture des fichiers HDF5. |
| Astropy | Coordonnées célestes, temps et unités astronomiques. |
| pandas | Manipulation des tables de résultats. |
| ipykernel | Exécution de notebooks avec cet environnement, si souhaité. |

La liste des dépendances provient du
[pyproject.toml de v3.1.0](https://github.com/nu-radio/NuRadioMC/blob/v3.1.0/pyproject.toml).

## 7. Vérifier GSL et indiquer son emplacement

GSL fournit les fonctions numériques C nécessaires à la version compilée du
ray tracer analytique. Homebrew l'a installée à l'étape 4.

```bash
export GSLDIR=/opt/homebrew/opt/gsl
"$GSLDIR/bin/gsl-config" --version
```

La commande doit afficher la version de GSL installée. La variable utilisée par
le script de compilation de NuRadioMC v3.1.0 est bien `GSLDIR`, sans underscore.

Source : [prérequis du ray tracer](https://github.com/nu-radio/NuRadioMC/blob/v3.1.0/NuRadioMC/SignalProp/CPPAnalyticRayTracing/README.md).

## 8. Compiler et vérifier le ray tracer

Avec `.venv` toujours actif et `GSLDIR` défini :

```bash
cd /Users/chiche/Desktop/GRBsRNO/.software/NuRadioMC/NuRadioMC/SignalProp/CPPAnalyticRayTracing
python setup.py build_ext --inplace
cd /Users/chiche/Desktop/GRBsRNO
python -c 'from NuRadioMC.SignalProp.CPPAnalyticRayTracing import wrapper; print("Ray tracer C++ : import OK")'
```

Cette compilation produit une extension native que Python peut importer. Elle
accélère les calculs de propagation. Un import réussi vérifie le chargement de
l'extension ; la simulation de contrôle plus bas vérifie son usage dans la chaîne.

## 9. Installer PROPOSAL pour les secondaires

Cette étape prépare la propagation des muons et taus. Elle est utile pour le
modèle complet ; ton premier exemple avec `proposal=False` peut fonctionner
sans elle.

```bash
export CONAN_HOME=/Users/chiche/Desktop/GRBsRNO/.software/conan
python -m pip install --no-build-isolation "proposal==7.6.2"
python -c 'import proposal; print("PROPOSAL : import OK")'
```

La version 7.6.2 correspond à la dépendance optionnelle déclarée par NuRadioMC
v3.1.0. Si une compilation est nécessaire, Conan récupère ses dépendances C++.
`CONAN_HOME` réserve un cache à ce projet. `--no-build-isolation` utilise les
outils de compilation installés à l'étape 5, notamment la version de CMake choisie.

Sources : [installation PROPOSAL 7.6.2](https://github.com/tudo-astroparticlephysics/PROPOSAL/blob/7.6.2/INSTALL.md),
[cache Conan](https://docs.conan.io/2/reference/environment.html#conan-home).

## 10. Contrôler les imports et les dépendances

```bash
python -m pip check
python -c 'import six, numpy, scipy, matplotlib, h5py, astropy, pandas, NuRadioMC, NuRadioReco; from NuRadioMC.EvtGen import generator; from NuRadioMC.utilities import Veff, cross_sections; print("Imports : OK"); print("NuRadioMC :", NuRadioMC.__version__); print("Code :", NuRadioMC.__file__)'
```

`pip check` cherche les incompatibilités de dépendances déclarées. Les imports
vérifient que les modules sont disponibles dans le bon environnement. Ils ne
remplacent pas une simulation complète.

Pour retester ton générateur dans un dossier dédié :

```bash
mkdir -p EffectiveAreas/env_check
cd EffectiveAreas/env_check
python ../01_generate_neutrino_events.py
cd /Users/chiche/Desktop/GRBsRNO
```

Le fichier HDF5 sera créé dans `EffectiveAreas/env_check`.

## 11. Faire une simulation de contrôle

Copie l'exemple officiel dans un dossier de travail :

```bash
cp -R .software/NuRadioMC/NuRadioMC/examples/01_Veff_simulation EffectiveAreas/smoke_test
cd EffectiveAreas/smoke_test
python T01generate_event_list.py
python T02RunSimulation.py 1e19_n1e3.hdf5 surface_station_1GHz.json config.yaml 1e19_n1e3_output.hdf5
cd /Users/chiche/Desktop/GRBsRNO
```

Cet exemple contrôle l'enchaînement génération, émission, propagation et trigger.
Il utilise un détecteur d'exemple, pas le modèle RNO-G final. Certains modèles
d'antennes ou bibliothèques d'émission peuvent être téléchargés au premier usage.
Un test avec `proposal=True` et la configuration Greenland sera aussi nécessaire
avant une production incluant les secondaires.

Source : [tutoriel effectif-volume](https://nu-radio.github.io/NuRadioMC/NuRadioMC/pages/Manuals/veff_tutorial.html).

## 12. Choisir cet environnement dans VS Code

Ouvre `GRBsRNO` dans VS Code, puis la palette de commandes avec `Cmd+Shift+P`.
Choisis **Python: Select Interpreter**, puis le chemin :

```text
/Users/chiche/Desktop/GRBsRNO/.venv/bin/python
```

Crée ensuite un nouveau terminal intégré. Vérifie à nouveau `sys.executable`.
Pour un notebook, sélectionne ce même environnement comme noyau Python.

Source : [environnements Python dans VS Code](https://code.visualstudio.com/docs/python/environments).

## 13. Enregistrer la configuration validée

Après réussite des tests :

```bash
python -m pip freeze > EffectiveAreas/requirements-rnog-frozen.txt
git -C .software/NuRadioMC rev-parse HEAD > EffectiveAreas/nuradiomc-commit.txt
python -VV > EffectiveAreas/python-version.txt
"$GSLDIR/bin/gsl-config" --version > EffectiveAreas/gsl-version.txt
```

Cela enregistre les versions réellement obtenues. Le fichier de packages contient
une référence éditable au dépôt local : pour reconstruire ailleurs, il faut aussi
recréer le checkout au commit enregistré, installer GSL et compiler les extensions. Il ne
s'agit donc pas, à lui seul, d'un environnement entièrement portable.

Ajoute `.venv/` et `.software/` aux chemins ignorés par Git ; conserve tes scripts,
configurations et références de versions dans le projet.

## À chaque nouvelle session

Quitte Conda s'il est activé, puis :

```bash
cd /Users/chiche/Desktop/GRBsRNO
source .venv/bin/activate
export GSLDIR=/opt/homebrew/opt/gsl
export CONAN_HOME=/Users/chiche/Desktop/GRBsRNO/.software/conan
```

Tu peux ensuite utiliser `python` pour les scripts du projet. Pour quitter le
venv, utilise `deactivate`.

La disponibilité des modèles de détecteur et l'accès éventuel à la base matérielle
RNO-G restent des entrées de la simulation. Installer les packages ne fournit pas
automatiquement ces descriptions ou ces accès.
