import 'package:flutter/material.dart';

import 'theme.dart';

class ProtoStrip extends StatelessWidget {
  const ProtoStrip({super.key});
  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        color: const Color(0xFFFFE9B5),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
        child: const Row(children: [
          Icon(Icons.science_outlined, size: 14, color: Color(0xFF6B4E00)),
          SizedBox(width: 6),
          Expanded(
            child: Text(
              'Prototype de démonstration - non validé cliniquement',
              style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF6B4E00)),
            ),
          ),
        ]),
      );
}

class AppScaffold extends StatelessWidget {
  final String title;
  final Widget body;
  final Widget? bottom;
  final List<Widget>? actions;
  const AppScaffold({
    super.key,
    required this.title,
    required this.body,
    this.bottom,
    this.actions,
  });

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(title), actions: actions),
        body: SafeArea(
          top: false,
          child: Column(children: [
            const ProtoStrip(),
            Expanded(child: body),
            if (bottom != null)
              Padding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                  child: bottom),
          ]),
        ),
      );
}

class StepHeader extends StatelessWidget {
  final int step;
  final int total;
  final String title;
  const StepHeader(
      {super.key, required this.step, required this.total, required this.title});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Étape $step sur $total',
            style: TextStyle(
                color: cs.primary, fontWeight: FontWeight.w700, fontSize: 13)),
        const SizedBox(height: 4),
        Text(title,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
        const SizedBox(height: 12),
        TweenAnimationBuilder<double>(
          tween: Tween(begin: 0, end: step / total),
          duration: const Duration(milliseconds: 500),
          curve: Curves.easeOutCubic,
          builder: (_, v, _) => ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(value: v, minHeight: 6),
          ),
        ),
      ]),
    );
  }
}

class SoftCard extends StatelessWidget {
  final Widget child;
  final Color? color;
  final EdgeInsetsGeometry padding;
  const SoftCard({
    super.key,
    required this.child,
    this.color,
    this.padding = const EdgeInsets.all(16),
  });

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: padding,
        decoration: BoxDecoration(
          color: color ?? Theme.of(context).colorScheme.surfaceContainerLow,
          borderRadius: BorderRadius.circular(20),
        ),
        child: child,
      );
}

class SectionTitle extends StatelessWidget {
  final String text;
  final String? subtitle;
  const SectionTitle(this.text, {super.key, this.subtitle});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(4, 18, 4, 8),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(text,
              style:
                  const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          if (subtitle != null)
            Text(subtitle!,
                style: TextStyle(
                    fontSize: 12.5,
                    color: Theme.of(context).colorScheme.onSurfaceVariant)),
        ]),
      );
}

class UrgencyBanner extends StatelessWidget {
  final String urgence;
  const UrgencyBanner(this.urgence, {super.key});
  @override
  Widget build(BuildContext context) {
    final c = urgenceColor(urgence);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
            colors: [c, Color.lerp(c, Colors.black, 0.25)!],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Row(children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
              color: Colors.white.withAlpha(45), shape: BoxShape.circle),
          child: Icon(urgenceIcon(urgence), color: Colors.white, size: 30),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(urgenceTitle(urgence),
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 21,
                    fontWeight: FontWeight.w800)),
            const SizedBox(height: 2),
            Text(urgenceHint(urgence),
                style: TextStyle(
                    color: Colors.white.withAlpha(225), fontSize: 13.5)),
          ]),
        ),
      ]),
    );
  }
}

class UrgencyChip extends StatelessWidget {
  final String urgence;
  const UrgencyChip(this.urgence, {super.key});
  @override
  Widget build(BuildContext context) {
    final c = urgenceColor(urgence);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
          color: c.withAlpha(30), borderRadius: BorderRadius.circular(20)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(urgenceIcon(urgence), size: 14, color: c),
        const SizedBox(width: 4),
        Text(urgenceTitle(urgence),
            style: TextStyle(
                color: c, fontSize: 12, fontWeight: FontWeight.w700)),
      ]),
    );
  }
}

class ProbBar extends StatelessWidget {
  final String label;
  final double value; // 0..1
  final Color? color;
  const ProbBar(
      {super.key, required this.label, required this.value, this.color});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final c = color ?? cs.primary;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(
              child: Text(label,
                  style: const TextStyle(
                      fontSize: 15, fontWeight: FontWeight.w600))),
          Text('${(value * 100).round()} %',
              style: TextStyle(fontWeight: FontWeight.w800, color: c)),
        ]),
        const SizedBox(height: 6),
        TweenAnimationBuilder<double>(
          tween: Tween(begin: 0, end: value.clamp(0.0, 1.0)),
          duration: const Duration(milliseconds: 700),
          curve: Curves.easeOutCubic,
          builder: (_, v, _) => ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: v,
              minHeight: 10,
              color: c,
              backgroundColor: cs.surfaceContainerHighest,
            ),
          ),
        ),
      ]),
    );
  }
}

class OptionTile extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const OptionTile(
      {super.key,
      required this.label,
      required this.selected,
      required this.onTap});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return AnimatedContainer(
      duration: const Duration(milliseconds: 180),
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: selected ? cs.primaryContainer : cs.surfaceContainerLow,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
            color: selected ? cs.primary : Colors.transparent, width: 2),
      ),
      child: Material(
        type: MaterialType.transparency,
        child: InkWell(
          borderRadius: BorderRadius.circular(18),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
            child: Row(children: [
              Expanded(
                  child: Text(label,
                      style: const TextStyle(
                          fontSize: 17, fontWeight: FontWeight.w600))),
              AnimatedOpacity(
                opacity: selected ? 1 : 0,
                duration: const Duration(milliseconds: 180),
                child: Icon(Icons.check_circle, color: cs.primary),
              ),
            ]),
          ),
        ),
      ),
    );
  }
}

class CornerFrame extends CustomPainter {
  final Color color;
  CornerFrame(this.color);

  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = color
      ..strokeWidth = 5
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;
    const l = 36.0, m = 14.0;
    final r = Rect.fromLTWH(m, m, size.width - 2 * m, size.height - 2 * m);
    void corner(Offset o, double dx, double dy) {
      canvas.drawLine(o, o + Offset(dx * l, 0), p);
      canvas.drawLine(o, o + Offset(0, dy * l), p);
    }

    corner(r.topLeft, 1, 1);
    corner(r.topRight, -1, 1);
    corner(r.bottomLeft, 1, -1);
    corner(r.bottomRight, -1, -1);
  }

  @override
  bool shouldRepaint(covariant CornerFrame old) => old.color != color;
}
