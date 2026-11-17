# Résultats préliminaires

## Configuration

- NuRadioMC : 3.1.0, commit `599eb0a9e6abb35277c661fc4a6e2cad0b6a75da`.
- Modèle des interactions : `ctw` ; seed : 12345.
- 50,000 neutrinos primaires, 61,805 lignes de showers.
- Énergie primaire : 1.00e+16 à 1.00e+20 eV.
- Volume de génération : 235.62 km³.
- Directions échantillonnées uniformément en cos(zenith) et en azimut dans les bornes du fichier.
- Interactions primaires uniquement, sans propagation des muons et des taus.

Il s'agit d'interactions forcées non pondérées dans le volume : les histogrammes
décrivent l'échantillonnage et la physique du générateur. Ils ne représentent pas
une population détectée, une aire effective ou un taux astrophysique. L'absorption
dans la Terre et la réponse de RNO-G restent à simuler.

Avec le choix CTW par défaut, la distribution d'inélasticité est indépendante de
l'énergie. Le modèle et ses hypothèses sont conservés ici explicitement pour
ce premier contrôle reproductible et utilisable hors ligne.

## Comptages

| Quantité | Valeur |
| --- | ---: |
| Neutrinos primaires | 50,000 |
| Interactions CC | 35,632 (71.26 %) |
| Interactions NC | 14,368 (28.74 %) |
| Showers hadroniques | 50,000 |
| Showers électromagnétiques | 11,805 |
| Inélasticité moyenne | 0.2108 |

| Saveur PDG | Neutrinos primaires |
| --- | ---: |
| 12 | 8,305 |
| -12 | 8,230 |
| 14 | 8,473 |
| -14 | 8,318 |
| 16 | 8,270 |
| -16 | 8,404 |

Un neutrino électronique en interaction CC produit deux showers : hadronique et
électromagnétique. Il compte une seule fois dans les histogrammes de neutrinos.
Les comptages utilisent les `event_group_ids` uniques, pas les lignes HDF5.
Les courbes de fraction CC comparent le Monte Carlo à sigma_CC/(sigma_CC+sigma_NC)
du modèle choisi ; les barres d'erreur sont des incertitudes binomiales de simulation.

## Contrôles

12 contrôles réussis : nombres de primaires/showers, identités,
bornes de génération, inélasticités et relations E_had=y E_nu,
E_em=(1-y) E_nu. Détails dans `summary.json`.

## Figures

PNG pour les diapositives, SVG pour une version vectorielle. Style Matplotlib
simple, sans titres. Les axes indiquent si l'on compte des neutrinos ou des showers.

- [01_neutrino_energy](figures/01_neutrino_energy.png)
- [02_arrival_directions](figures/02_arrival_directions.png)
- [03_interaction_vertices](figures/03_interaction_vertices.png)
- [04_flavours_and_interactions](figures/04_flavours_and_interactions.png)
- [05_inelasticity](figures/05_inelasticity.png)
- [06_cc_fraction](figures/06_cc_fraction.png)
- [07_shower_energies_and_multiplicity](figures/07_shower_energies_and_multiplicity.png)
- [08_askaryan_example](figures/08_askaryan_example.png)
- [00_overview](figures/00_overview.png)

## Exemple radio séparé

La figure radio, si présente, utilise une shower hadronique de 1 EeV à 1 km,
dans une glace homogène d'indice 1.78, avec Alvarez2009. Les trois angles sont
l'angle de Cherenkov, puis +1 et +2 degrés. Le spectre est normalisé au maximum
du spectre à l'angle de Cherenkov, commun aux trois courbes. Il n'inclut ni
atténuation de la glace, ni firn, ni antenne, ni bruit, ni trigger. Il illustre
le module d'émission ; ce n'est pas une simulation complète du détecteur.

## Suite scientifique

Valider une station et son trigger, choisir les modèles de production avec la
collaboration, ajouter l'absorption terrestre et les secondaires, puis simuler
les 35 stations et calculer A_eff(E, theta, phi) avec les incertitudes associées.
