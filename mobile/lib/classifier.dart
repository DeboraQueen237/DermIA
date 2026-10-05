import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/foundation.dart' show compute;
import 'package:flutter/services.dart' show rootBundle;
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';

/// Score d'une classe du modèle (probabilité calibrée).
class ClassScore {
  final String label;
  final double p;
  const ClassScore(this.label, this.p);
}

/// Correspondance classes du modèle -> identifiants de la base de connaissances.
const modelToKb = {
  'gale': 'gale',
  'teigne_mycose': 'teigne',
  'impetigo': 'impetigo',
  'eczema': 'eczema',
  'tungiase': 'tungiase',
  'buruli': 'buruli',
  'lepre': 'lepre',
  'pian': 'pian',
};

class _PrepArgs {
  final String path;
  final int size;
  final bool nchw;
  const _PrepArgs(this.path, this.size, this.nchw);
}

const _mean = [0.485, 0.456, 0.406];
const _std = [0.229, 0.224, 0.225];

/// Prétraitement dans un isolate : redimensionne et normalise (ImageNet).
Float32List _prep(_PrepArgs a) {
  final decoded = img.decodeImage(File(a.path).readAsBytesSync());
  if (decoded == null) throw Exception('image illisible');
  final r = img.copyResize(decoded,
      width: a.size, height: a.size, interpolation: img.Interpolation.linear);
  final s = a.size;
  final n = s * s;
  final out = Float32List(3 * n);
  for (var y = 0; y < s; y++) {
    for (var x = 0; x < s; x++) {
      final px = r.getPixel(x, y);
      final v0 = (px.r / 255.0 - _mean[0]) / _std[0];
      final v1 = (px.g / 255.0 - _mean[1]) / _std[1];
      final v2 = (px.b / 255.0 - _mean[2]) / _std[2];
      if (a.nchw) {
        final i = y * s + x;
        out[i] = v0;
        out[n + i] = v1;
        out[2 * n + i] = v2;
      } else {
        final i = (y * s + x) * 3;
        out[i] = v0;
        out[i + 1] = v1;
        out[i + 2] = v2;
      }
    }
  }
  return out;
}

/// Charge `assets/model/dermia.tflite` + `labels.json` s'ils existent.
/// Sinon `available` reste faux et l'application fonctionne sans modèle d'image.
class SkinClassifier {
  Interpreter? _interp;
  List<String> labels = [];
  bool _nchw = true;
  int _size = 224;
  bool _loaded = false;

  bool get available => _interp != null;

  Future<void> load() async {
    if (_loaded) return;
    _loaded = true;
    try {
      final raw = await rootBundle.loadString('assets/model/labels.json');
      labels = List<String>.from(jsonDecode(raw) as List);
      final opts = InterpreterOptions()..threads = 2;
      final it = await Interpreter.fromAsset('assets/model/dermia.tflite',
          options: opts);
      final shape = it.getInputTensor(0).shape;
      _nchw = shape[1] == 3;
      _size = _nchw ? shape[2] : shape[1];
      _interp = it;
    } catch (_) {
      _interp = null; // modèle absent : mode questionnaire seul
    }
  }

  /// Retourne les classes triées par probabilité décroissante, ou null.
  Future<List<ClassScore>?> predict(String path) async {
    final it = _interp;
    if (it == null) return null;
    final s = _size;
    final flat = await compute(_prep, _PrepArgs(path, s, _nchw));
    final Object input = _nchw
        ? [
            List.generate(
                3,
                (c) => List.generate(
                    s, (y) => List.generate(s, (x) => flat[c * s * s + y * s + x])))
          ]
        : [
            List.generate(
                s,
                (y) => List.generate(
                    s, (x) => List.generate(3, (c) => flat[(y * s + x) * 3 + c])))
          ];
    final output = [List<double>.filled(labels.length, 0.0)];
    it.run(input, output);
    final scores = [
      for (var i = 0; i < labels.length; i++) ClassScore(labels[i], output[0][i])
    ]..sort((a, b) => b.p.compareTo(a.p));
    return scores;
  }
}

final classifier = SkinClassifier();
