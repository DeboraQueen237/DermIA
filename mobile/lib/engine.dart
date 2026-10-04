import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart' show rootBundle;
import 'package:image/image.dart' as img;
import 'package:path_provider/path_provider.dart';

// ---------------------------------------------------------------------------
// Base de connaissances (assets/kb/diseases.json) - BROUILLON non validé
// ---------------------------------------------------------------------------

class Disease {
  final String id;
  final String nom;
  final String urgence; // standard | prioritaire
  final List<String> signes;
  final List<String> alertes;
  final List<String> conduite;
  final List<String> prevention;

  Disease.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        nom = j['nom'] as String,
        urgence = j['urgence'] as String,
        signes = List<String>.from(j['signes'] as List),
        alertes = List<String>.from(j['alertes'] as List),
        conduite = List<String>.from(j['conduite'] as List),
        prevention = List<String>.from(j['prevention'] as List);
}

class KnowledgeBase {
  final String version;
  final List<Disease> diseases;
  KnowledgeBase(this.version, this.diseases);

  static Future<KnowledgeBase> load() async {
    final raw = await rootBundle.loadString('assets/kb/diseases.json');
    final j = jsonDecode(raw) as Map<String, dynamic>;
    final list = (j['maladies'] as List)
        .map((e) => Disease.fromJson(e as Map<String, dynamic>))
        .toList();
    return KnowledgeBase(j['version'] as String, list);
  }
}

// ---------------------------------------------------------------------------
// Questionnaire
// ---------------------------------------------------------------------------

class Question {
  final String key;
  final String label;
  final Map<String, String> options;
  const Question(this.key, this.label, this.options);
}

const questions = <Question>[
  Question('aspect', 'Aspect principal de la lésion', {
    'ulcere': 'Plaie ouverte / ulcère',
    'nodule': 'Bosse, nodule ou gonflement',
    'tache': 'Tache claire ou rougeâtre',
    'plaque_ronde': 'Plaque ronde avec squames',
    'croutes': 'Croûtes jaunâtres',
    'grattage': 'Petits boutons avec traces de grattage',
  }),
  Question('sensibilite', 'Sensibilité de la zone (toucher avec du coton)', {
    'normale': 'Normale',
    'perdue': 'Diminuée ou absente',
    'inconnue': 'Non testée',
  }),
  Question('douleur', 'La lésion est-elle douloureuse ?', {
    'oui': 'Oui',
    'non': 'Non',
  }),
  Question('demangeaison', 'Démangeaisons', {
    'aucune': 'Aucune',
    'moderee': 'Modérées',
    'intense_nuit': 'Intenses, surtout la nuit',
  }),
  Question('duree', 'Depuis combien de temps ?', {
    'court': 'Moins de 2 semaines',
    'moyen': '2 semaines à 3 mois',
    'long': 'Plus de 3 mois',
  }),
  Question('foyer', 'D\'autres personnes du foyer sont-elles atteintes ?', {
    'oui': 'Oui',
    'non': 'Non',
  }),
  Question('age', 'Le patient est', {
    'enfant': 'Un enfant (moins de 15 ans)',
    'adulte': 'Un adulte',
  }),
  Question('fievre', 'Fièvre ?', {
    'oui': 'Oui',
    'non': 'Non',
  }),
];

// ---------------------------------------------------------------------------
// Moteur de triage par règles (PROTOTYPE - non validé cliniquement)
// Remplacé / complété plus tard par le modèle d'images + fusion clinique.
// ---------------------------------------------------------------------------

class Hypothesis {
  final Disease disease;
  final double share; // part relative des signes concordants, PAS une probabilité
  Hypothesis(this.disease, this.share);
}

class Triage {
  final List<Hypothesis> top;
  final bool indeterminate;
  final String urgence; // standard | prioritaire | urgente
  final List<String> alertes;
  Triage(this.top, this.indeterminate, this.urgence, this.alertes);
}

const _urgenceRank = {'standard': 0, 'prioritaire': 1, 'urgente': 2};

Triage triage(Map<String, String> a, KnowledgeBase kb) {
  final s = <String, double>{for (final d in kb.diseases) d.id: 0};
  void add(String id, double v) {
    if (s.containsKey(id)) s[id] = s[id]! + v;
  }

  final aspect = a['aspect'];
  final sens = a['sensibilite'];
  final douleur = a['douleur'];
  final dem = a['demangeaison'];
  final duree = a['duree'];
  final foyer = a['foyer'];
  final age = a['age'];

  // Ulcère de Buruli
  if (aspect == 'ulcere') add('buruli', 3);
  if (aspect == 'nodule') add('buruli', 2);
  if ((aspect == 'ulcere' || aspect == 'nodule') && douleur == 'non') {
    add('buruli', 2);
  }
  if (duree == 'moyen' || duree == 'long') add('buruli', 1);

  // Lèpre
  if (aspect == 'tache') add('lepre', 3);
  if (aspect == 'nodule') add('lepre', 1);
  if (sens == 'perdue') add('lepre', 4);
  if (douleur == 'non') add('lepre', 1);
  if (dem == 'aucune') add('lepre', 1);
  if (duree == 'long') add('lepre', 2);
  if (foyer == 'oui') add('lepre', 1);

  // Gale
  if (dem == 'intense_nuit') add('gale', 4);
  if (aspect == 'grattage') add('gale', 3);
  if (foyer == 'oui') add('gale', 3);
  if (duree == 'court' || duree == 'moyen') add('gale', 1);

  // Teigne
  if (aspect == 'plaque_ronde') add('teigne', 4);
  if (dem == 'moderee') add('teigne', 1);
  if (age == 'enfant') add('teigne', 1);

  // Impétigo
  if (aspect == 'croutes') add('impetigo', 4);
  if (age == 'enfant') add('impetigo', 2);
  if (duree == 'court') add('impetigo', 1);

  // Pian
  if (age == 'enfant') add('pian', 2);
  if (douleur == 'non') add('pian', 1);
  if (aspect == 'croutes' || aspect == 'ulcere' || aspect == 'nodule') {
    add('pian', 1);
  }
  if (duree == 'moyen') add('pian', 1);
  if (foyer == 'oui') add('pian', 1);

  final ranked = kb.diseases.where((d) => s[d.id]! > 0).toList()
    ..sort((x, y) => s[y.id]!.compareTo(s[x.id]!));
  final top3 = ranked.take(3).toList();
  final total = top3.fold<double>(0, (p, d) => p + s[d.id]!);
  final hyps = [
    for (final d in top3) Hypothesis(d, total == 0 ? 0 : s[d.id]! / total),
  ];

  final best = top3.isEmpty ? 0.0 : s[top3.first.id]!;
  final indeterminate = best < 4;

  var level = indeterminate
      ? 'prioritaire'
      : (top3.first.urgence == 'prioritaire' ? 'prioritaire' : 'standard');
  final alertes = <String>[];

  if (a['fievre'] == 'oui') {
    alertes.add('Fièvre associée à une lésion cutanée : avis d\'un soignant sans délai.');
    level = 'urgente';
  }
  if (sens == 'perdue') {
    alertes.add('Perte de sensibilité : évoquer la lèpre, référer pour examen.');
    if (_urgenceRank[level]! < 1) level = 'prioritaire';
  }
  if (indeterminate) {
    alertes.add('Signes insuffisants ou atypiques : ne pas conclure, référer.');
  }
  return Triage(hyps, indeterminate, level, alertes);
}

// ---------------------------------------------------------------------------
// Contrôle qualité de la photo (flou, luminosité) - seuils à calibrer
// ---------------------------------------------------------------------------

class ImageQuality {
  final bool ok;
  final List<String> messages;
  ImageQuality(this.ok, this.messages);
}

/// Exécutée dans un isolate. Retourne [variance du laplacien, luminosité moyenne].
List<double> analyzeImage(String path) {
  final decoded = img.decodeImage(File(path).readAsBytesSync());
  if (decoded == null) return [-1, -1];
  final small = img.copyResize(decoded, width: 256);
  final w = small.width, h = small.height;
  final lum = List<double>.generate(
      w * h, (i) => small.getPixel(i % w, i ~/ w).luminance.toDouble());
  var sum = 0.0;
  for (final v in lum) {
    sum += v;
  }
  final mean = sum / lum.length;
  var s = 0.0, s2 = 0.0;
  var n = 0;
  for (var y = 1; y < h - 1; y++) {
    for (var x = 1; x < w - 1; x++) {
      final c = lum[y * w + x];
      final l = 4 * c -
          lum[(y - 1) * w + x] -
          lum[(y + 1) * w + x] -
          lum[y * w + x - 1] -
          lum[y * w + x + 1];
      s += l;
      s2 += l * l;
      n++;
    }
  }
  final variance = s2 / n - (s / n) * (s / n);
  return [variance, mean];
}

ImageQuality qualityFrom(List<double> m) {
  if (m[0] < 0) return ImageQuality(false, ['Image illisible, reprenez la photo.']);
  final msgs = <String>[];
  if (m[0] < 30) msgs.add('Photo floue : tenez le téléphone stable et refaites la mise au point.');
  if (m[1] < 60) msgs.add('Photo trop sombre : placez le patient à la lumière du jour.');
  if (m[1] > 205) msgs.add('Photo surexposée : évitez le soleil direct et le flash.');
  return ImageQuality(msgs.isEmpty, msgs);
}

// ---------------------------------------------------------------------------
// Historique local (JSON dans le stockage privé de l'app).
// TODO phase 2 : SQLCipher + clé dans l'Android Keystore.
// ---------------------------------------------------------------------------

class CaseRecord {
  final String id;
  final String date;
  final String? imagePath;
  final Map<String, String> answers;
  final List<Map<String, dynamic>> top; // {id, nom, share}
  final String urgence;
  final bool indeterminate;
  final bool research;

  CaseRecord({
    required this.id,
    required this.date,
    required this.imagePath,
    required this.answers,
    required this.top,
    required this.urgence,
    required this.indeterminate,
    required this.research,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'date': date,
        'imagePath': imagePath,
        'answers': answers,
        'top': top,
        'urgence': urgence,
        'indeterminate': indeterminate,
        'research': research,
      };

  factory CaseRecord.fromJson(Map<String, dynamic> j) => CaseRecord(
        id: j['id'] as String,
        date: j['date'] as String,
        imagePath: j['imagePath'] as String?,
        answers: Map<String, String>.from(j['answers'] as Map),
        top: (j['top'] as List)
            .map((e) => Map<String, dynamic>.from(e as Map))
            .toList(),
        urgence: j['urgence'] as String,
        indeterminate: j['indeterminate'] as bool,
        research: j['research'] as bool,
      );
}

class CaseStore {
  static Future<File> _file() async {
    final d = await getApplicationDocumentsDirectory();
    return File('${d.path}/cases.json');
  }

  static Future<List<CaseRecord>> all() async {
    final f = await _file();
    if (!await f.exists()) return [];
    final list = jsonDecode(await f.readAsString()) as List;
    return list
        .map((e) => CaseRecord.fromJson(e as Map<String, dynamic>))
        .toList()
        .reversed
        .toList();
  }

  static Future<void> add(CaseRecord r) async {
    final f = await _file();
    final List current =
        await f.exists() ? jsonDecode(await f.readAsString()) as List : [];
    current.add(r.toJson());
    await f.writeAsString(jsonEncode(current));
  }

  static Future<String> keepImage(String src, String id) async {
    final d = await getApplicationDocumentsDirectory();
    final dir = Directory('${d.path}/images');
    await dir.create(recursive: true);
    final dest = '${dir.path}/$id.jpg';
    await File(src).copy(dest);
    return dest;
  }
}
