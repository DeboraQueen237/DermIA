import 'package:flutter/material.dart';

class Brand {
  static const teal = Color(0xFF0F766E);
  static const tealDark = Color(0xFF0B4F4A);
  static const urgent = Color(0xFFC62828);
  static const priority = Color(0xFFE65100);
  static const standard = Color(0xFF2E7D32);
}

ThemeData buildTheme(Brightness b) {
  final scheme = ColorScheme.fromSeed(seedColor: Brand.teal, brightness: b);
  RoundedRectangleBorder round(double r) =>
      RoundedRectangleBorder(borderRadius: BorderRadius.circular(r));
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: scheme.surface,
    appBarTheme: AppBarTheme(
      backgroundColor: scheme.surface,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
          fontSize: 20, fontWeight: FontWeight.w700, color: scheme.onSurface),
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      color: scheme.surfaceContainerLow,
      margin: const EdgeInsets.symmetric(vertical: 6),
      shape: round(20),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size.fromHeight(56),
        shape: round(16),
        textStyle: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(52),
        shape: round(16),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),
    pageTransitionsTheme: const PageTransitionsTheme(builders: {
      TargetPlatform.android: ZoomPageTransitionsBuilder(),
    }),
  );
}

Color urgenceColor(String u) => switch (u) {
      'urgente' => Brand.urgent,
      'prioritaire' => Brand.priority,
      _ => Brand.standard,
    };

IconData urgenceIcon(String u) => switch (u) {
      'urgente' => Icons.emergency,
      'prioritaire' => Icons.local_hospital,
      _ => Icons.healing,
    };

String urgenceTitle(String u) => switch (u) {
      'urgente' => 'Référer sans délai',
      'prioritaire' => 'Référer rapidement',
      _ => 'Soins de première ligne',
    };

String urgenceHint(String u) => switch (u) {
      'urgente' => 'Avis d\'un soignant le jour même.',
      'prioritaire' => 'Orienter vers un centre de santé dans les prochains jours.',
      _ => 'Prise en charge locale et surveillance de l\'évolution.',
    };

int urgenceRank(String u) => switch (u) { 'urgente' => 2, 'prioritaire' => 1, _ => 0 };
