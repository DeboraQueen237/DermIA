import 'dart:io';
import 'dart:math';

import 'package:flutter/foundation.dart' show compute;
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'engine.dart';

class PrototypeBanner extends StatelessWidget {
  const PrototypeBanner({super.key});
  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        color: Colors.amber.shade200,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        child: const Text(
          'PROTOTYPE DE DÉMONSTRATION - non validé cliniquement. '
          'Ne remplace pas un soignant.',
          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        ),
      );
}

class CaseDraft {
  bool consent = false;
  bool research = false;
  String? imagePath;
  final Map<String, String> answers = {};
}

// ---------------------------------------------------------------------------
// 1. Consentement
// ---------------------------------------------------------------------------

class ConsentScreen extends StatefulWidget {
  const ConsentScreen({super.key});
  @override
  State<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends State<ConsentScreen> {
  final draft = CaseDraft();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Consentement')),
      body: Column(children: [
        const PrototypeBanner(),
        Expanded(
          child: ListView(padding: const EdgeInsets.all(16), children: [
            const Text(
              'Expliquez au patient (ou à son parent) :\n\n'
              '• une photo de la peau va être prise, sans visage ni nom ;\n'
              '• elle aide à orienter vers les bons soins ;\n'
              '• l\'outil peut se tromper : un soignant décide ;\n'
              '• il peut refuser sans perdre l\'accès aux soins.',
              style: TextStyle(fontSize: 16, height: 1.4),
            ),
            const SizedBox(height: 16),
            CheckboxListTile(
              value: draft.consent,
              onChanged: (v) => setState(() => draft.consent = v ?? false),
              title: const Text('Le patient accepte la prise de photo et l\'usage de l\'outil'),
              controlAffinity: ListTileControlAffinity.leading,
            ),
            CheckboxListTile(
              value: draft.research,
              onChanged: (v) => setState(() => draft.research = v ?? false),
              title: const Text('Optionnel : accepte l\'usage de la photo pour la recherche'),
              subtitle: const Text('Sans effet sur les soins.'),
              controlAffinity: ListTileControlAffinity.leading,
            ),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: draft.consent
                  ? () => Navigator.push(context,
                      MaterialPageRoute(builder: (_) => CaptureScreen(draft: draft)))
                  : null,
              child: const Text('Continuer'),
            ),
          ),
        ),
      ]),
    );
  }
}

// ---------------------------------------------------------------------------
// 2. Capture photo + contrôle qualité
// ---------------------------------------------------------------------------

class CaptureScreen extends StatefulWidget {
  final CaseDraft draft;
  const CaptureScreen({super.key, required this.draft});
  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  final _picker = ImagePicker();
  ImageQuality? _quality;
  bool _busy = false;

  Future<void> _pick(ImageSource src) async {
    final f = await _picker.pickImage(
        source: src, maxWidth: 1024, imageQuality: 85);
    if (f == null) return;
    setState(() {
      _busy = true;
      widget.draft.imagePath = f.path;
      _quality = null;
    });
    final m = await compute(analyzeImage, f.path);
    if (!mounted) return;
    setState(() {
      _quality = qualityFrom(m);
      _busy = false;
    });
  }

  void _next() => Navigator.push(
      context,
      MaterialPageRoute(
          builder: (_) => QuestionnaireScreen(draft: widget.draft)));

  @override
  Widget build(BuildContext context) {
    final path = widget.draft.imagePath;
    final q = _quality;
    return Scaffold(
      appBar: AppBar(title: const Text('Photo de la lésion')),
      body: Column(children: [
        const PrototypeBanner(),
        Expanded(
          child: ListView(padding: const EdgeInsets.all(16), children: [
            const Text(
              'Lumière du jour, à 15-20 cm, lésion au centre, avec un peu de '
              'peau saine autour. Pas de visage ni de bijoux.',
              style: TextStyle(fontSize: 15),
            ),
            const SizedBox(height: 12),
            if (path != null)
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.file(File(path), height: 280, fit: BoxFit.cover),
              ),
            const SizedBox(height: 12),
            if (_busy) const LinearProgressIndicator(),
            if (q != null)
              Card(
                color: q.ok ? Colors.green.shade50 : Colors.orange.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: q.ok
                      ? const Text('Qualité correcte.')
                      : Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [for (final m in q.messages) Text('• $m')]),
                ),
              ),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(
                  child: FilledButton.icon(
                      onPressed: () => _pick(ImageSource.camera),
                      icon: const Icon(Icons.photo_camera),
                      label: const Text('Prendre'))),
              const SizedBox(width: 8),
              Expanded(
                  child: OutlinedButton.icon(
                      onPressed: () => _pick(ImageSource.gallery),
                      icon: const Icon(Icons.photo_library),
                      label: const Text('Galerie'))),
            ]),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: Column(children: [
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: (path != null && q != null && q.ok) ? _next : null,
                child: const Text('Continuer'),
              ),
            ),
            if (path != null && q != null && !q.ok)
              TextButton(
                  onPressed: _next,
                  child: const Text('Continuer malgré tout')),
          ]),
        ),
      ]),
    );
  }
}

// ---------------------------------------------------------------------------
// 3. Questionnaire
// ---------------------------------------------------------------------------

class QuestionnaireScreen extends StatefulWidget {
  final CaseDraft draft;
  const QuestionnaireScreen({super.key, required this.draft});
  @override
  State<QuestionnaireScreen> createState() => _QuestionnaireScreenState();
}

class _QuestionnaireScreenState extends State<QuestionnaireScreen> {
  @override
  Widget build(BuildContext context) {
    final a = widget.draft.answers;
    final complete = questions.every((q) => a.containsKey(q.key));
    return Scaffold(
      appBar: AppBar(title: const Text('Questions cliniques')),
      body: Column(children: [
        const PrototypeBanner(),
        Expanded(
          child: ListView(padding: const EdgeInsets.all(16), children: [
            for (final q in questions) ...[
              Text(q.label,
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Wrap(spacing: 8, runSpacing: 4, children: [
                for (final e in q.options.entries)
                  ChoiceChip(
                    label: Text(e.value),
                    selected: a[q.key] == e.key,
                    onSelected: (_) => setState(() => a[q.key] = e.key),
                  ),
              ]),
              const SizedBox(height: 18),
            ],
          ]),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: complete
                  ? () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => ResultScreen(draft: widget.draft)))
                  : null,
              child: const Text('Voir l\'orientation'),
            ),
          ),
        ),
      ]),
    );
  }
}

// ---------------------------------------------------------------------------
// 4. Résultat + conduite à tenir
// ---------------------------------------------------------------------------

String urgenceLabel(String u) => switch (u) {
      'urgente' => 'Référer SANS DÉLAI',
      'prioritaire' => 'Référer rapidement vers un centre de santé',
      _ => 'Soins de première ligne et surveillance',
    };

Color urgenceColor(String u) => switch (u) {
      'urgente' => Colors.red.shade100,
      'prioritaire' => Colors.orange.shade100,
      _ => Colors.green.shade100,
    };

class ResultScreen extends StatefulWidget {
  final CaseDraft draft;
  const ResultScreen({super.key, required this.draft});
  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  late Future<KnowledgeBase> _kb;
  bool _saved = false;

  @override
  void initState() {
    super.initState();
    _kb = KnowledgeBase.load();
  }

  Future<void> _save(Triage t) async {
    final id = '${DateTime.now().millisecondsSinceEpoch}-${Random().nextInt(9999)}';
    final p = widget.draft.imagePath;
    final kept = p == null ? null : await CaseStore.keepImage(p, id);
    await CaseStore.add(CaseRecord(
      id: id,
      date: DateTime.now().toIso8601String(),
      imagePath: kept,
      answers: Map.of(widget.draft.answers),
      top: [
        for (final h in t.top)
          {'id': h.disease.id, 'nom': h.disease.nom, 'share': h.share}
      ],
      urgence: t.urgence,
      indeterminate: t.indeterminate,
      research: widget.draft.research,
    ));
    if (!mounted) return;
    setState(() => _saved = true);
    Navigator.of(context).popUntil((r) => r.isFirst);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Orientation')),
      body: FutureBuilder<KnowledgeBase>(
        future: _kb,
        builder: (context, snap) {
          if (snap.hasError) {
            return Center(child: Text('Erreur base de connaissances : ${snap.error}'));
          }
          if (!snap.hasData) return const Center(child: CircularProgressIndicator());
          final t = triage(widget.draft.answers, snap.data!);
          return Column(children: [
            const PrototypeBanner(),
            Expanded(
              child: ListView(padding: const EdgeInsets.all(16), children: [
                Card(
                  color: urgenceColor(t.urgence),
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Text(urgenceLabel(t.urgence),
                        style: const TextStyle(
                            fontSize: 18, fontWeight: FontWeight.bold)),
                  ),
                ),
                for (final a in t.alertes)
                  ListTile(
                      leading: const Icon(Icons.warning_amber, color: Colors.deepOrange),
                      title: Text(a)),
                const SizedBox(height: 8),
                Text(
                  t.indeterminate
                      ? 'Hypothèses (faible concordance - ne pas conclure) :'
                      : 'Signes évocateurs de :',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 6),
                for (final h in t.top) _DiseaseCard(h),
                const SizedBox(height: 12),
                const Text(
                  'La « concordance » compare uniquement les signes saisis entre '
                  'eux ; ce n\'est PAS une probabilité. Cette version n\'analyse '
                  'pas encore l\'image avec un modèle d\'IA. Contenu médical en '
                  'cours de relecture clinique.',
                  style: TextStyle(fontSize: 12, color: Colors.black54),
                ),
              ]),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: _saved ? null : () => _save(t),
                  icon: const Icon(Icons.save),
                  label: const Text('Enregistrer le cas'),
                ),
              ),
            ),
          ]);
        },
      ),
    );
  }
}

class _DiseaseCard extends StatelessWidget {
  final Hypothesis h;
  const _DiseaseCard(this.h);

  Widget _section(String title, List<String> items) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
          for (final i in items) Text('• $i'),
        ]),
      );

  @override
  Widget build(BuildContext context) {
    final d = h.disease;
    return Card(
      child: ExpansionTile(
        title: Text(d.nom, style: const TextStyle(fontWeight: FontWeight.w700)),
        subtitle: Text('Concordance des signes : ${(h.share * 100).round()} %'),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
        expandedCrossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _section('Signes évocateurs', d.signes),
          _section('Signes d\'alerte', d.alertes),
          _section('Conduite à tenir', d.conduite),
          _section('Prévention', d.prevention),
        ],
      ),
    );
  }
}
