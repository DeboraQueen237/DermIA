import 'dart:io';

import 'package:flutter/material.dart';

import 'engine.dart';
import 'flow.dart';

void main() => runApp(const DermIAApp());

class DermIAApp extends StatelessWidget {
  const DermIAApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'DermIA',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0F766E)),
          useMaterial3: true,
        ),
        home: const HomeScreen(),
      );
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('DermIA')),
      body: Column(children: [
        const PrototypeBanner(),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Icon(Icons.health_and_safety, size: 72, color: Color(0xFF0F766E)),
                const SizedBox(height: 12),
                const Text(
                  'Aide à l\'orientation pour les maladies de peau tropicales.\n'
                  'Fonctionne sans connexion.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16),
                ),
                const SizedBox(height: 32),
                FilledButton.icon(
                  onPressed: () => Navigator.push(context,
                      MaterialPageRoute(builder: (_) => const ConsentScreen())),
                  icon: const Icon(Icons.add_a_photo),
                  label: const Padding(
                    padding: EdgeInsets.all(14),
                    child: Text('Nouveau cas', style: TextStyle(fontSize: 18)),
                  ),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: () => Navigator.push(context,
                      MaterialPageRoute(builder: (_) => const HistoryScreen())),
                  icon: const Icon(Icons.history),
                  label: const Padding(
                    padding: EdgeInsets.all(12),
                    child: Text('Historique des cas'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ]),
    );
  }
}

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Historique')),
      body: FutureBuilder<List<CaseRecord>>(
        future: CaseStore.all(),
        builder: (context, snap) {
          if (!snap.hasData) return const Center(child: CircularProgressIndicator());
          final cases = snap.data!;
          if (cases.isEmpty) return const Center(child: Text('Aucun cas enregistré.'));
          return ListView.separated(
            itemCount: cases.length,
            separatorBuilder: (_, _) => const Divider(height: 1),
            itemBuilder: (context, i) {
              final c = cases[i];
              final best = c.top.isEmpty ? 'Indéterminé' : c.top.first['nom'] as String;
              final date = c.date.substring(0, 16).replaceFirst('T', ' ');
              return ListTile(
                leading: c.imagePath == null
                    ? const Icon(Icons.image_not_supported)
                    : ClipRRect(
                        borderRadius: BorderRadius.circular(6),
                        child: Image.file(File(c.imagePath!),
                            width: 48, height: 48, fit: BoxFit.cover)),
                title: Text(c.indeterminate ? 'Indéterminé - référer' : best),
                subtitle: Text('$date · ${urgenceLabel(c.urgence)}'),
                tileColor: urgenceColor(c.urgence).withAlpha(90),
              );
            },
          );
        },
      ),
    );
  }
}
