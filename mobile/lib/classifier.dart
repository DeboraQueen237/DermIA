import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter/foundation.dart' show compute, debugPrint;
import 'package:flutter/services.dart' show rootBundle;
import 'package:image/image.dart' as img;
import 'package:onnxruntime/onnxruntime.dart';

// ---------------------------------------------------------------------------
// Types publics
// ---------------------------------------------------------------------------

/// Score d'une classe du modèle (probabilité calibrée).
class ClassScore {
  final String label;
  final double p;
  const ClassScore(this.label, this.p);
}

/// Correspondance classes du modèle -> identifiants de la base de connaissances.
///
/// Seules les classes présentes dans la KB contribuent au triage.
/// Les classes HAM10000 (melanome, naevus, carcinome_basal, etc.) sont
/// affichées à titre informatif mais pas encore exploitées par le moteur.
const modelToKb = <String, String>{
  'lepre': 'lepre',
};

// ---------------------------------------------------------------------------
// Prétraitement d'image (exécuté dans un isolate)
// ---------------------------------------------------------------------------

class _PrepArgs {
  final String path;
  final int size;
  const _PrepArgs(this.path, this.size);
}

const _mean = <double>[0.485, 0.456, 0.406];
const _std = <double>[0.229, 0.224, 0.225];

/// Prétraitement dans un isolate : redimensionne + normalise (ImageNet, NCHW).
///
/// Sortie : Float32List de taille [3 * size * size] en layout NCHW.
Float32List _prep(_PrepArgs a) {
  final decoded = img.decodeImage(File(a.path).readAsBytesSync());
  if (decoded == null) {
    throw Exception('Image illisible : ${a.path}');
  }

  final resized = img.copyResize(
    decoded,
    width: a.size,
    height: a.size,
    interpolation: img.Interpolation.linear,
  );

  final s = a.size;
  final n = s * s;
  final out = Float32List(3 * n);

  for (var y = 0; y < s; y++) {
    for (var x = 0; x < s; x++) {
      final px = resized.getPixel(x, y);
      final i = y * s + x;
      out[i] = (px.r / 255.0 - _mean[0]) / _std[0];
      out[n + i] = (px.g / 255.0 - _mean[1]) / _std[1];
      out[2 * n + i] = (px.b / 255.0 - _mean[2]) / _std[2];
    }
  }

  return out;
}

// ---------------------------------------------------------------------------
// Classifieur ONNX Runtime
// ---------------------------------------------------------------------------

/// Classifieur ONNX Runtime (modèle unifié 8 classes).
///
/// Charge `assets/model/dermia_unified.onnx` + `assets/model/metadata.json`.
/// Si le chargement échoue, `available` reste faux et l'application
/// fonctionne en mode questionnaire seul.
class SkinClassifier {
  OrtSession? _session;
  List<String> labels = <String>[];
  int _size = 300;
  double _temperature = 1.0;
  bool _loaded = false;

  /// Indique si le modèle est chargé et prêt à l'inférence.
  bool get available => _session != null;

  /// Charge le modèle ONNX et ses métadonnées.
  Future<void> load() async {
    if (_loaded) return;
    _loaded = true;

    try {
      // 1. Métadonnées
      final metaRaw = await rootBundle.loadString(
        'assets/model/metadata.json',
      );
      final meta = jsonDecode(metaRaw) as Map<String, dynamic>;

      labels = List<String>.from(meta['classes'] as List);
      _size = (meta['img_size'] as num).toInt();
      _temperature = (meta['temperature'] as num).toDouble();

      debugPrint(
        '[Classifier] ${labels.length} classes, '
        'size=$_size, T=$_temperature',
      );

      // 2. Session ONNX
      final raw = await rootBundle.load(
        'assets/model/dermia_unified.onnx',
      );
      final bytes = raw.buffer.asUint8List();

      OrtEnv.instance.init();
      final opts = OrtSessionOptions();
      _session = OrtSession.fromBuffer(bytes, opts);

      debugPrint('[Classifier] Modèle ONNX chargé avec succès');
    } catch (e, st) {
      debugPrint('[Classifier] Erreur de chargement : $e\n$st');
      _session = null;
    }
  }

  /// Retourne les classes triées par probabilité décroissante, ou null
  /// si le modèle n'est pas disponible.
  Future<List<ClassScore>?> predict(String path) async {
    final session = _session;
    if (session == null) return null;

    final s = _size;
    final flat = await compute(_prep, _PrepArgs(path, s));

    // Tensor d'entrée NCHW : [1, 3, s, s]
    final inputOrt = OrtValueTensor.createTensorWithDataList(
      flat,
      <int>[1, 3, s, s],
    );

    final inputs = <String, OrtValue>{'input': inputOrt};
    final runOptions = OrtRunOptions();

    List<OrtValue?>? outputs;
    try {
      outputs = await session.runAsync(runOptions, inputs);
    } finally {
      inputOrt.release();
      runOptions.release();
    }

    if (outputs == null || outputs.isEmpty || outputs[0] == null) {
      if (outputs != null) {
        for (final o in outputs) {
          o?.release();
        }
      }
      return null;
    }

    // Sortie : [[logit_0, ..., logit_N]]
    final raw = outputs[0]!.value as List;
    final row = raw[0] as List;
    final logits = <double>[
      for (final v in row) (v as num).toDouble(),
    ];

    for (final o in outputs) {
      o?.release();
    }

    // Softmax avec température (calibration clinique)
    final scaled = <double>[
      for (final v in logits) v / _temperature,
    ];
    final maxV = scaled.reduce(math.max);
    final expV = <double>[
      for (final v in scaled) math.exp(v - maxV),
    ];
    final sumExp = expV.reduce((a, b) => a + b);
    final probs = <double>[
      for (final v in expV) v / sumExp,
    ];

    final scores = <ClassScore>[
      for (var i = 0; i < labels.length; i++)
        ClassScore(labels[i], probs[i]),
    ]..sort((a, b) => b.p.compareTo(a.p));

    return scores;
  }
}

/// Instance globale du classifieur.
final SkinClassifier classifier = SkinClassifier();