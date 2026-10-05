import 'dart:io';
import 'dart:math';

import 'package:flutter/foundation.dart' show compute;
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'classifier.dart';
import 'engine.dart';
import 'theme.dart';
import 'widgets.dart';

const _steps = 4;

// ═══════════════════════════════════════════════════════════════════════════════
// Draft
// ═══════════════════════════════════════════════════════════════════════════════

class CaseDraft {
  bool consent = false;
  bool research = false;
  String? imagePath;
  final Map<String, String> answers = {};
}

// ═══════════════════════════════════════════════════════════════════════════════
// 1 – Consentement
// ═══════════════════════════════════════════════════════════════════════════════

class ConsentScreen extends StatefulWidget {
  const ConsentScreen({super.key});
  @override
  State<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends State<ConsentScreen> {
  final draft = CaseDraft();

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return AppScaffold(
      title: 'Consentement',
      bottom: SizedBox(
        width: double.infinity,
        child: FilledButton(
          onPressed: draft.consent
              ? () => Navigator.push(context,
                  MaterialPageRoute(builder: (_) => CaptureScreen(draft: draft)))
              : null,
          child: const Text('Continuer'),
        ),
      ),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        const StepHeader(step: 1, total: _steps, title: 'Consentement du patient'),
        SoftCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                    color: cs.primaryContainer,
                    borderRadius: BorderRadius.circular(14)),
                child: Icon(Icons.privacy_tip_rounded,
                    color: cs.primary, size: 24),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Text('Expliquez au patient',
                    style:
                        TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
              ),
            ]),
            const SizedBox(height: 16),
            const Text(
              '• Une photo de la peau va être prise, sans visage ni nom\n'
              '• Elle aide à orienter vers les bons soins\n'
              '• L\'outil peut se tromper : un soignant décide\n'
              '• Le patient peut refuser sans perdre l\'accès aux soins',
              style: TextStyle(fontSize: 15, height: 1.6),
            ),
          ]),
        ),
        const SizedBox(height: 20),
        _Toggle(
          value: draft.consent,
          onChanged: (v) => setState(() => draft.consent = v),
          title: 'Le patient accepte la prise de photo et l\'usage de l\'outil',
          required: true,
        ),
        const SizedBox(height: 10),
        _Toggle(
          value: draft.research,
          onChanged: (v) => setState(() => draft.research = v),
          title: 'Optionnel : accepte l\'usage pour la recherche',
          subtitle: 'Sans effet sur les soins.',
          required: false,
        ),
      ]),
    );
  }
}

class _Toggle extends StatelessWidget {
  final bool value, required;
  final ValueChanged<bool> onChanged;
  final String title;
  final String? subtitle;
  const _Toggle(
      {required this.value,
      required this.onChanged,
      required this.title,
      this.subtitle,
      required this.required});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      decoration: BoxDecoration(
        color: value ? cs.primaryContainer.withAlpha(80) : cs.surfaceContainerLow,
        borderRadius: BorderRadius.circular(18),
        border:
            Border.all(color: value ? cs.primary : Colors.transparent, width: 2),
      ),
      child: Material(
        type: MaterialType.transparency,
        child: InkWell(
          borderRadius: BorderRadius.circular(18),
          onTap: () => onChanged(!value),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(children: [
              AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  color: value ? cs.primary : Colors.transparent,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                      color: value ? cs.primary : cs.outline, width: 2),
                ),
                child: value
                    ? const Icon(Icons.check, color: Colors.white, size: 18)
                    : null,
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title,
                          style: const TextStyle(
                              fontSize: 15, fontWeight: FontWeight.w600)),
                      if (subtitle != null) ...[
                        const SizedBox(height: 2),
                        Text(subtitle!,
                            style: TextStyle(
                                fontSize: 12.5, color: cs.onSurfaceVariant)),
                      ],
                    ]),
              ),
              if (required)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                      color: cs.error.withAlpha(20),
                      borderRadius: BorderRadius.circular(8)),
                  child: Text('Requis',
                      style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: cs.error)),
                ),
            ]),
          ),
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 2 – Capture photo
// ═══════════════════════════════════════════════════════════════════════════════

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
    final f =
        await _picker.pickImage(source: src, maxWidth: 1024, imageQuality: 85);
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

  void _next() => Navigator.push(context,
      MaterialPageRoute(builder: (_) => QuestionnaireScreen(draft: widget.draft)));

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final path = widget.draft.imagePath;
    final q = _quality;
    return AppScaffold(
      title: 'Photo',
      bottom: Column(mainAxisSize: MainAxisSize.min, children: [
        SizedBox(
          width: double.infinity,
          child: FilledButton(
            onPressed: (path != null && q != null && q.ok) ? _next : null,
            child: const Text('Continuer'),
          ),
        ),
        if (path != null && q != null && !q.ok)
          TextButton(onPressed: _next, child: const Text('Continuer malgré tout')),
      ]),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        const StepHeader(step: 2, total: _steps, title: 'Photo de la lésion'),
        SoftCard(
          padding: const EdgeInsets.all(14),
          child: Row(children: [
            Icon(Icons.lightbulb_rounded, color: cs.primary, size: 20),
            const SizedBox(width: 10),
            const Expanded(
              child: Text(
                'Lumière du jour, 15-20 cm, lésion au centre, '
                'un peu de peau saine autour. Pas de visage.',
                style: TextStyle(fontSize: 14, height: 1.4),
              ),
            ),
          ]),
        ),
        const SizedBox(height: 16),

        // preview
        AspectRatio(
          aspectRatio: 1,
          child: path != null
              ? Stack(children: [
                  Positioned.fill(
                    child: ClipRRect(
                        borderRadius: BorderRadius.circular(24),
                        child: Image.file(File(path), fit: BoxFit.cover)),
                  ),
                  Positioned.fill(
                      child: CustomPaint(painter: CornerFrame(cs.primary))),
                ])
              : Container(
                  decoration: BoxDecoration(
                    color: cs.surfaceContainerHighest.withAlpha(80),
                    borderRadius: BorderRadius.circular(24),
                  ),
                  child: Stack(children: [
                    Center(
                      child: Column(mainAxisSize: MainAxisSize.min, children: [
                        Icon(Icons.camera_alt_rounded,
                            size: 56,
                            color: cs.onSurfaceVariant.withAlpha(80)),
                        const SizedBox(height: 12),
                        Text('Prenez une photo',
                            style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: cs.onSurfaceVariant)),
                      ]),
                    ),
                    Positioned.fill(
                        child: CustomPaint(
                            painter: CornerFrame(cs.primary.withAlpha(80)))),
                  ]),
                ),
        ),

        const SizedBox(height: 14),
        if (_busy) ...[const LinearProgressIndicator(), const SizedBox(height: 8)],

        if (q != null)
          SoftCard(
            color: (q.ok ? Brand.standard : Brand.priority).withAlpha(20),
            padding: const EdgeInsets.all(14),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Icon(q.ok ? Icons.check_circle_rounded : Icons.info_rounded,
                  color: q.ok ? Brand.standard : Brand.priority, size: 22),
              const SizedBox(width: 10),
              Expanded(
                child: q.ok
                    ? const Text('Qualité correcte',
                        style: TextStyle(fontWeight: FontWeight.w600))
                    : Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [for (final m in q.messages) Text('• $m')]),
              ),
            ]),
          ),

        const SizedBox(height: 16),
        Row(children: [
          Expanded(
              child: FilledButton.icon(
                  onPressed: () => _pick(ImageSource.camera),
                  icon: const Icon(Icons.photo_camera_rounded),
                  label: const Text('Prendre'))),
          const SizedBox(width: 10),
          Expanded(
              child: OutlinedButton.icon(
                  onPressed: () => _pick(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library_rounded),
                  label: const Text('Galerie'))),
        ]),
      ]),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 3 – Questionnaire (one question per page)
// ═══════════════════════════════════════════════════════════════════════════════

class QuestionnaireScreen extends StatefulWidget {
  final CaseDraft draft;
  const QuestionnaireScreen({super.key, required this.draft});
  @override
  State<QuestionnaireScreen> createState() => _QuestionnaireScreenState();
}

class _QuestionnaireScreenState extends State<QuestionnaireScreen> {
  int _page = 0;

  @override
  Widget build(BuildContext context) {
    final a = widget.draft.answers;
    final q = questions[_page];
    final isLast = _page == questions.length - 1;

    return AppScaffold(
      title: 'Questionnaire',
      bottom: Row(children: [
        if (_page > 0) ...[
          OutlinedButton(
              onPressed: () => setState(() => _page--),
              child: const Text('Précédent')),
          const SizedBox(width: 12),
        ],
        Expanded(
          child: FilledButton(
            onPressed: a.containsKey(q.key)
                ? () {
                    if (isLast) {
                      Navigator.push(
                          context,
                          MaterialPageRoute(
                              builder: (_) =>
                                  ResultScreen(draft: widget.draft)));
                    } else {
                      setState(() => _page++);
                    }
                  }
                : null,
            child: Text(isLast ? 'Voir l\'orientation' : 'Suivant'),
          ),
        ),
      ]),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        StepHeader(
            step: 3,
            total: _steps,
            title: 'Question ${_page + 1} / ${questions.length}'),
        const SizedBox(height: 4),
        Text(q.label,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
        const SizedBox(height: 20),
        for (final e in q.options.entries)
          OptionTile(
              label: e.value,
              selected: a[q.key] == e.key,
              onTap: () => setState(() => a[q.key] = e.key)),
      ]),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 4 – Résultat + conduite à tenir
// ═══════════════════════════════════════════════════════════════════════════════

class _AnalysisResult {
  final KnowledgeBase kb;
  final Triage triage;
  final bool usedAi;
  _AnalysisResult(this.kb, this.triage, this.usedAi);
}

class ResultScreen extends StatefulWidget {
  final CaseDraft draft;
  const ResultScreen({super.key, required this.draft});
  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen>
    with SingleTickerProviderStateMixin {
  late final Future<_AnalysisResult> _analysis;
  late final AnimationController _anim;
  bool _saved = false;

  @override
  void initState() {
    super.initState();
    _anim = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 800));
    _analysis = _run();
  }

  Future<_AnalysisResult> _run() async {
    final kb = await KnowledgeBase.load();

    // Run AI classifier if available
    Map<String, double>? imageScores;
    if (classifier.available && widget.draft.imagePath != null) {
      final scores = await classifier.predict(widget.draft.imagePath!);
      if (scores != null) {
        imageScores = {};
        for (final cs in scores) {
          final kbId = modelToKb[cs.label];
          if (kbId != null) imageScores[kbId] = cs.p;
        }
      }
    }

    final t = triage(widget.draft.answers, kb, imageScores: imageScores);
    _anim.forward();
    return _AnalysisResult(kb, t, imageScores != null);
  }

  Future<void> _save(Triage t) async {
    final id =
        '${DateTime.now().millisecondsSinceEpoch}-${Random().nextInt(9999)}';
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
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: const Text('Cas enregistré avec succès'),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ));
    Navigator.of(context).popUntil((r) => r.isFirst);
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_AnalysisResult>(
      future: _analysis,
      builder: (context, snap) {
        if (snap.hasError) {
          return AppScaffold(
              title: 'Erreur',
              body: Center(child: Text('${snap.error}')));
        }
        if (!snap.hasData) {
          return AppScaffold(title: 'Analyse', body: const _Loading());
        }
        final r = snap.data!;
        final t = r.triage;
        return AppScaffold(
          title: 'Orientation',
          bottom: SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: _saved ? null : () => _save(t),
              icon: const Icon(Icons.save_rounded),
              label: const Text('Enregistrer le cas'),
            ),
          ),
          body: FadeTransition(
            opacity: _anim,
            child: ListView(padding: const EdgeInsets.all(20), children: [
              const StepHeader(step: 4, total: _steps, title: 'Résultat'),
              const SizedBox(height: 4),

              UrgencyBanner(t.urgence),
              const SizedBox(height: 14),

              // alerts
              for (final a in t.alertes) ...[
                SoftCard(
                  color: Brand.priority.withAlpha(18),
                  padding: const EdgeInsets.all(14),
                  child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.warning_amber_rounded,
                            color: Brand.priority, size: 22),
                        const SizedBox(width: 10),
                        Expanded(
                            child: Text(a,
                                style: const TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600))),
                      ]),
                ),
                const SizedBox(height: 8),
              ],

              // analysis mode
              SoftCard(
                padding: const EdgeInsets.all(12),
                child: Row(children: [
                  Icon(
                      r.usedAi
                          ? Icons.smart_toy_rounded
                          : Icons.rule_rounded,
                      size: 18,
                      color: Theme.of(context).colorScheme.primary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      r.usedAi
                          ? 'Analyse combinée : image IA + questionnaire'
                          : 'Analyse par questionnaire uniquement',
                      style: const TextStyle(fontSize: 12.5),
                    ),
                  ),
                ]),
              ),

              SectionTitle(
                t.indeterminate
                    ? 'Hypothèses (faible concordance)'
                    : 'Signes évocateurs de',
                subtitle:
                    t.indeterminate ? 'Ne pas conclure — référer' : null,
              ),

              for (final h in t.top) ProbBar(label: h.disease.nom, value: h.share),
              const SizedBox(height: 14),
              for (final h in t.top) _DiseaseDetail(h),

              const SizedBox(height: 16),
              Text(
                'Ce résultat compare les signes saisis ; '
                'ce n\'est PAS un diagnostic. Un soignant qualifié '
                'doit confirmer. Contenu médical en cours de relecture.',
                style: TextStyle(
                    fontSize: 12,
                    color: Theme.of(context).colorScheme.onSurfaceVariant),
              ),
            ]),
          ),
        );
      },
    );
  }
}

// ── Loading ──────────────────────────────────────────────────────────────────

class _Loading extends StatelessWidget {
  const _Loading();
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Center(
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        SizedBox(
            width: 64,
            height: 64,
            child: CircularProgressIndicator(strokeWidth: 5, color: cs.primary)),
        const SizedBox(height: 24),
        Text('Analyse en cours…',
            style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: cs.onSurface)),
        const SizedBox(height: 8),
        Text('Photo et questionnaire en cours de traitement',
            style: TextStyle(fontSize: 14, color: cs.onSurfaceVariant)),
      ]),
    );
  }
}

// ── Disease detail card ──────────────────────────────────────────────────────

class _DiseaseDetail extends StatelessWidget {
  final Hypothesis h;
  const _DiseaseDetail(this.h);

  Widget _section(BuildContext ctx, String title, List<String> items) {
    final cs = Theme.of(ctx).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title,
            style: TextStyle(
                fontWeight: FontWeight.w700, fontSize: 14, color: cs.primary)),
        const SizedBox(height: 4),
        for (final i in items)
          Padding(
            padding: const EdgeInsets.only(bottom: 3),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('• ', style: TextStyle(color: cs.onSurfaceVariant)),
              Expanded(child: Text(i, style: const TextStyle(fontSize: 14, height: 1.4))),
            ]),
          ),
      ]),
    );
  }

  @override
  Widget build(BuildContext context) {
    final d = h.disease;
    return SoftCard(
      padding: EdgeInsets.zero,
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          expandedCrossAxisAlignment: CrossAxisAlignment.start,
          shape: const Border(),
          title: Text(d.nom,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          subtitle: Text(
            '${d.urgence == 'prioritaire' ? '⚠ Référer' : '🟢 1ère ligne'} · '
            '${d.signes.length} signes',
            style: const TextStyle(fontSize: 13),
          ),
          children: [
            _section(context, 'Signes évocateurs', d.signes),
            _section(context, 'Signes d\'alerte', d.alertes),
            _section(context, 'Conduite à tenir', d.conduite),
            _section(context, 'Prévention', d.prevention),
          ],
        ),
      ),
    );
  }
}
