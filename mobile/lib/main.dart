import 'dart:io';

import 'package:flutter/material.dart';

import 'classifier.dart';
import 'engine.dart';
import 'flow.dart';
import 'theme.dart';
import 'widgets.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  classifier.load();
  runApp(const DermIAApp());
}

class DermIAApp extends StatelessWidget {
  const DermIAApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'DermIA',
        debugShowCheckedModeBanner: false,
        theme: buildTheme(Brightness.light),
        home: const HomeScreen(),
      );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Home
// ═══════════════════════════════════════════════════════════════════════════════

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen>
    with SingleTickerProviderStateMixin {
  int _total = 0, _today = 0, _urgent = 0;
  late final AnimationController _anim;

  @override
  void initState() {
    super.initState();
    _anim = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1000))
      ..forward();
    _refresh();
  }

  Future<void> _refresh() async {
    final all = await CaseStore.all();
    final now = DateTime.now();
    if (!mounted) return;
    setState(() {
      _total = all.length;
      _today = all.where((c) {
        final d = DateTime.tryParse(c.date);
        return d != null &&
            d.year == now.year &&
            d.month == now.month &&
            d.day == now.day;
      }).length;
      _urgent = all.where((c) => c.urgence == 'urgente').length;
    });
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  Widget _stagger(double from, Widget child) => FadeTransition(
        opacity: CurvedAnimation(
            parent: _anim, curve: Interval(from, 1, curve: Curves.easeOut)),
        child: SlideTransition(
          position: Tween(begin: const Offset(0, 0.06), end: Offset.zero)
              .animate(CurvedAnimation(
                  parent: _anim,
                  curve: Interval(from, 1, curve: Curves.easeOutCubic))),
          child: child,
        ),
      );

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          const ProtoStrip(),
          Expanded(
            child: RefreshIndicator(
              onRefresh: _refresh,
              child: ListView(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 40),
                children: [
                  // ── Brand ─────────────────────────────
                  _stagger(0.0, Row(children: [
                    Container(
                      padding: const EdgeInsets.all(15),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                            colors: [Brand.teal, Brand.tealDark]),
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: [
                          BoxShadow(
                              color: Brand.teal.withAlpha(50),
                              blurRadius: 14,
                              offset: const Offset(0, 5)),
                        ],
                      ),
                      child: const Icon(Icons.health_and_safety_rounded,
                          color: Colors.white, size: 30),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('DermIA',
                                style: TextStyle(
                                    fontSize: 30,
                                    fontWeight: FontWeight.w900,
                                    color: cs.onSurface,
                                    letterSpacing: -0.5)),
                            Text('Aide au triage dermatologique',
                                style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w500,
                                    color: cs.onSurfaceVariant)),
                          ]),
                    ),
                  ])),

                  const SizedBox(height: 26),

                  // ── Hero Card ─────────────────────────
                  _stagger(
                    0.12,
                    Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Brand.teal, Brand.tealDark],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(28),
                        boxShadow: [
                          BoxShadow(
                              color: Brand.teal.withAlpha(70),
                              blurRadius: 28,
                              offset: const Offset(0, 10)),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.white.withAlpha(35),
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: const Icon(Icons.medical_services_rounded,
                                color: Colors.white, size: 26),
                          ),
                          const SizedBox(height: 18),
                          const Text('Orientez vos patients\nvers les bons soins',
                              style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 22,
                                  fontWeight: FontWeight.w800,
                                  height: 1.3)),
                          const SizedBox(height: 10),
                          Text(
                            'Photo + questions cliniques → hypothèses '
                            'avec niveau de confiance + conduite à tenir.\n'
                            'Fonctionne 100 % hors ligne.',
                            style: TextStyle(
                                color: Colors.white.withAlpha(200),
                                fontSize: 14,
                                height: 1.45),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 20),

                  // ── Stats ─────────────────────────────
                  _stagger(
                    0.22,
                    Row(children: [
                      Expanded(
                          child: _StatChip(Icons.folder_open_rounded,
                              '$_total', 'Total', Brand.teal)),
                      const SizedBox(width: 10),
                      Expanded(
                          child: _StatChip(Icons.today_rounded, '$_today',
                              "Aujourd'hui", const Color(0xFF6366F1))),
                      const SizedBox(width: 10),
                      Expanded(
                          child: _StatChip(Icons.warning_rounded,
                              '$_urgent', 'Urgents', Brand.urgent)),
                    ]),
                  ),

                  const SizedBox(height: 28),

                  // ── Nouveau cas ───────────────────────
                  _stagger(
                    0.32,
                    Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(24),
                        onTap: () async {
                          await Navigator.push(
                              context,
                              MaterialPageRoute(
                                  builder: (_) => const ConsentScreen()));
                          _refresh();
                        },
                        child: Ink(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 24, vertical: 22),
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                                colors: [Brand.teal, Color(0xFF059669)]),
                            borderRadius: BorderRadius.circular(24),
                            boxShadow: [
                              BoxShadow(
                                  color: Brand.teal.withAlpha(55),
                                  blurRadius: 18,
                                  offset: const Offset(0, 7)),
                            ],
                          ),
                          child: Row(children: [
                            Container(
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: Colors.white.withAlpha(40),
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: const Icon(Icons.add_a_photo_rounded,
                                  color: Colors.white, size: 28),
                            ),
                            const SizedBox(width: 18),
                            const Expanded(
                              child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Nouveau cas',
                                        style: TextStyle(
                                            color: Colors.white,
                                            fontSize: 20,
                                            fontWeight: FontWeight.w800)),
                                    SizedBox(height: 3),
                                    Text('Photo + questionnaire → orientation',
                                        style: TextStyle(
                                            color: Colors.white70,
                                            fontSize: 13)),
                                  ]),
                            ),
                            const Icon(Icons.arrow_forward_ios_rounded,
                                color: Colors.white54, size: 18),
                          ]),
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 14),

                  // ── Historique ─────────────────────────
                  _stagger(
                    0.40,
                    _ActionTile(
                      icon: Icons.history_rounded,
                      title: 'Historique des cas',
                      subtitle: '$_total cas enregistrés',
                      onTap: () async {
                        await Navigator.push(
                            context,
                            MaterialPageRoute(
                                builder: (_) => const HistoryScreen()));
                        _refresh();
                      },
                    ),
                  ),

                  const SizedBox(height: 24),

                  // ── AI status ─────────────────────────
                  _stagger(0.50, _AiStatusBar()),
                ],
              ),
            ),
          ),
        ]),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Home – private widgets
// ═══════════════════════════════════════════════════════════════════════════════

class _StatChip extends StatelessWidget {
  final IconData icon;
  final String value, label;
  final Color color;
  const _StatChip(this.icon, this.value, this.label, this.color);

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 10),
        decoration: BoxDecoration(
          color: color.withAlpha(18),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(height: 8),
          Text(value,
              style: TextStyle(
                  fontSize: 24, fontWeight: FontWeight.w900, color: color)),
          const SizedBox(height: 2),
          Text(label,
              style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: color.withAlpha(180))),
        ]),
      );
}

class _ActionTile extends StatelessWidget {
  final IconData icon;
  final String title, subtitle;
  final VoidCallback onTap;
  const _ActionTile(
      {required this.icon,
      required this.title,
      required this.subtitle,
      required this.onTap});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Material(
      color: cs.surfaceContainerLow,
      borderRadius: BorderRadius.circular(24),
      child: InkWell(
        borderRadius: BorderRadius.circular(24),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Row(children: [
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                  color: cs.primaryContainer,
                  borderRadius: BorderRadius.circular(16)),
              child: Icon(icon, color: cs.primary, size: 26),
            ),
            const SizedBox(width: 18),
            Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title,
                        style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w700,
                            color: cs.onSurface)),
                    const SizedBox(height: 2),
                    Text(subtitle,
                        style: TextStyle(
                            fontSize: 13, color: cs.onSurfaceVariant)),
                  ]),
            ),
            Icon(Icons.arrow_forward_ios_rounded,
                color: cs.onSurfaceVariant.withAlpha(120), size: 18),
          ]),
        ),
      ),
    );
  }
}

class _AiStatusBar extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final ok = classifier.available;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cs.surfaceContainerLow,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
            color: ok ? Brand.standard.withAlpha(40) : Colors.transparent),
      ),
      child: Row(children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: (ok ? Brand.standard : cs.onSurfaceVariant).withAlpha(20),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(
            ok ? Icons.smart_toy_rounded : Icons.psychology_alt_rounded,
            color: ok ? Brand.standard : cs.onSurfaceVariant,
            size: 18,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(ok ? 'Modèle IA actif' : 'Mode questionnaire',
                    style: const TextStyle(
                        fontSize: 13, fontWeight: FontWeight.w700)),
                Text(
                    ok
                        ? 'Analyse d\'image + questionnaire combinés'
                        : 'Pas de modèle chargé — orientation par règles cliniques',
                    style: TextStyle(
                        fontSize: 11.5, color: cs.onSurfaceVariant)),
              ]),
        ),
      ]),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// History
// ═══════════════════════════════════════════════════════════════════════════════

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});
  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  late Future<List<CaseRecord>> _future;

  @override
  void initState() {
    super.initState();
    _future = CaseStore.all();
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return AppScaffold(
      title: 'Historique',
      body: FutureBuilder<List<CaseRecord>>(
        future: _future,
        builder: (context, snap) {
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final cases = snap.data!;
          if (cases.isEmpty) {
            return Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Icon(Icons.folder_open_rounded,
                    size: 64, color: cs.onSurfaceVariant.withAlpha(80)),
                const SizedBox(height: 16),
                Text('Aucun cas enregistré',
                    style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                        color: cs.onSurfaceVariant)),
                const SizedBox(height: 6),
                Text('Les cas analysés apparaîtront ici.',
                    style: TextStyle(
                        fontSize: 14,
                        color: cs.onSurfaceVariant.withAlpha(150))),
              ]),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: cases.length,
            itemBuilder: (_, i) => _CaseCard(cases[i]),
          );
        },
      ),
    );
  }
}

class _CaseCard extends StatelessWidget {
  final CaseRecord c;
  const _CaseCard(this.c);

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final best = c.top.isEmpty ? 'Indéterminé' : c.top.first['nom'] as String;
    final date = c.date.substring(0, 16).replaceFirst('T', ' ');
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: cs.surfaceContainerLow,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(14),
            child: c.imagePath != null && File(c.imagePath!).existsSync()
                ? Image.file(File(c.imagePath!),
                    width: 58, height: 58, fit: BoxFit.cover)
                : Container(
                    width: 58,
                    height: 58,
                    color: cs.surfaceContainerHighest,
                    child: Icon(Icons.image_not_supported_rounded,
                        color: cs.onSurfaceVariant.withAlpha(80), size: 24),
                  ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(c.indeterminate ? 'Indéterminé — référer' : best,
                      style: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.w700),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis),
                  const SizedBox(height: 4),
                  Text(date,
                      style: TextStyle(
                          fontSize: 13, color: cs.onSurfaceVariant)),
                  const SizedBox(height: 6),
                  UrgencyChip(c.urgence),
                ]),
          ),
        ]),
      ),
    );
  }
}
