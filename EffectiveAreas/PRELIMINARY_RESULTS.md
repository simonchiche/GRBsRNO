# Résultats pour la réunion

Depuis la racine de `GRBsRNO`, une seule commande :

```bash
./EffectiveAreas/run_preliminary_results.sh
```

Le lanceur sélectionne directement le Python de `.venv`, sans activation manuelle.
Il fonctionne depuis n'importe quel dossier si son chemin est absolu. La commande
Python équivalente est `.venv/bin/python EffectiveAreas/make_preliminary_results.py`.
Il utilise un backend Matplotlib sans interface graphique et un cache local au
projet. Aucun package supplémentaire n'est nécessaire dans le venv déjà préparé.

## Fichiers produits

Tout se trouve dans `EffectiveAreas/preliminary_results/` :

- `neutrino_events.hdf5` : interactions et showers générées par NuRadioMC.
- `figures/00_overview.png` : six panneaux pour une vue d'ensemble.
- `figures/01_neutrino_energy.png` : énergies primaires.
- `figures/02_arrival_directions.png` : zenith, cos(zenith), azimut et attentes d'échantillonnage.
- `figures/03_interaction_vertices.png` : positions horizontales, profondeur et rayon.
- `figures/04_flavours_and_interactions.png` : saveurs et fractions CC/NC.
- `figures/05_inelasticity.png` : distribution de l'inélasticité.
- `figures/06_cc_fraction.png` : fraction CC selon l'énergie et comparaison avec les sections efficaces.
- `figures/07_shower_energies_and_multiplicity.png` : énergies et nombre de showers par neutrino.
- `figures/08_askaryan_example.png` : illustration séparée du module d'émission radio.
- Les mêmes figures en `.svg`, pour une version vectorielle.
- `summary.md` : paramètres, résultats et interprétation en français.
- `summary.json` : résultats, contrôles et provenance lisibles par une machine.
- `interaction_counts.csv` : comptages par saveur.
- `radio_example.csv` : traces électriques de l'illustration radio.

Les figures utilisent un style proche de Matplotlib par défaut, sans titre.

## Hypothèses du jeu par défaut

50 000 neutrinos primaires, six espèces équiprobables, énergie uniforme en
log(E) entre 10^16 et 10^20 eV, directions isotropes sur 4 pi, interactions
dans un cylindre de rayon 5 km entre z=-3 km et la surface, seed 12345.

Le modèle CTW est sélectionné explicitement pour fonctionner hors ligne. Dans
ce modèle, l'inélasticité utilise une distribution indépendante de l'énergie.
La fraction CC/NC utilise les sections efficaces à chaque énergie. La propagation
des leptons secondaires est désactivée.

Les histogrammes décrivent des **interactions forcées non pondérées**. Ils ne
représentent ni un flux astrophysique, ni des événements détectés, ni une aire
effective. Tous les comptages de neutrinos regroupent les lignes par
`event_group_ids` : deux showers ne sont pas deux neutrinos.

L'exemple radio utilise Alvarez2009, une shower hadronique de 1 EeV à 1 km,
dans une glace homogène d'indice 1.78, à trois angles de visée. Il est indépendant
du tirage de neutrinos et n'inclut ni firn, ni atténuation, ni réponse des antennes,
ni bruit, ni trigger. Les paramètres détaillés sont dans `summary.json`.

## Refaire ou adapter les figures

Une seconde exécution réutilise le même HDF5 si la configuration correspond et
reconstruit les figures. Pour un autre échantillon, utilise un dossier distinct :

```bash
.venv/bin/python EffectiveAreas/make_preliminary_results.py \
  --events 100000 --seed 42 \
  --output EffectiveAreas/preliminary_results_seed42
```

Pour utiliser un fichier d'entrée existant, sans créer d'événements :

```bash
.venv/bin/python EffectiveAreas/make_preliminary_results.py \
  --input chemin/vers/entree.hdf5 \
  --output EffectiveAreas/preliminary_existing
```

Cette option attend un fichier du générateur avec interactions primaires
uniquement, pas un fichier de sorties filtrées du détecteur. Sans modèle enregistré
dans l'entrée, la comparaison théorique de la fraction CC est omise.

Pour sélectionner le modèle BGR18 de NuRadioMC :

```bash
.venv/bin/python EffectiveAreas/make_preliminary_results.py \
  --model hedis_bgr18 --output EffectiveAreas/preliminary_bgr18
```

Le premier usage de BGR18 peut télécharger sa table de sections efficaces.
L'option `--regenerate` remplace explicitement l'échantillon du dossier choisi.
`--skip-radio-example` produit uniquement les diagnostics du générateur.

Le programme s'arrête si les relations physiques élémentaires ou les identifiants
ne sont pas cohérents ; les contrôles réussis sont enregistrés dans la synthèse.

## Ce que l'on peut présenter

- Un environnement NuRadioMC opérationnel pour générer et analyser les interactions.
- Un premier échantillon reproductible et des contrôles des distributions tirées.
- La distinction entre neutrinos primaires et showers, avec vérification du partage d'énergie.
- Une comparaison de la fraction CC générée avec celle du modèle d'interaction.
- Une première utilisation illustrée du module d'émission Askaryan.

La suite du projet est la simulation de propagation, des antennes et du trigger,
puis le calcul des aires effectives directionnelles de l'array.
