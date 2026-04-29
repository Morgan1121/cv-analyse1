#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CV Analyser Pro - Application Flask
Analyse de CV par intelligence artificielle avec Claude (Anthropic)
"""

from flask import Flask, render_template_string, request, jsonify, session
import json
import os
import re
from werkzeug.utils import secure_filename
from typing import List, Dict, Any, Optional
import uuid

# Si vous utilisez l'API Anthropic, décommentez la ligne suivante
# import anthropic

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['UPLOAD_FOLDER'] = 'uploads'

# Configuration - Remplacez par votre clé API Anthropic
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', 'votre-cle-api-anthropic-ici')

# Initialisation du client Anthropic (décommentez si vous avez la librairie)
# client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Assurez-vous que le dossier uploads existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============================================================================
# CONFIGURATION DES GRADES
# ============================================================================

GRADE_CONFIG = {
    'A': {'color': '#00b894', 'label': 'Excellent', 'emoji': '★★★★★'},
    'B': {'color': '#a29bfe', 'label': 'Très bien', 'emoji': '★★★★☆'},
    'C': {'color': '#fdcb6e', 'label': 'Bien', 'emoji': '★★★☆☆'},
    'D': {'color': '#e17055', 'label': 'Passable', 'emoji': '★★☆☆☆'},
    'F': {'color': '#d63031', 'label': 'Insuffisant', 'emoji': '★☆☆☆☆'}
}


def get_grade(score: int) -> str:
    """Détermine le grade basé sur le score"""
    if not isinstance(score, (int, float)) or score < 0:
        return 'F'
    if score >= 85:
        return 'A'
    elif score >= 70:
        return 'B'
    elif score >= 55:
        return 'C'
    elif score >= 40:
        return 'D'
    else:
        return 'F'


def clean_json_response(text: str) -> str:
    """Nettoie la réponse JSON de l'API"""
    # Supprimer les blocs de code markdown
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Supprimer les espaces au début et à la fin
    text = text.strip()
    
    # Trouver la première accolade et la dernière
    start = text.find('{')
    end = text.rfind('}') + 1
    
    if start >= 0 and end > start:
        text = text[start:end]
    
    return text


def analyze_cv_with_ai(cv_text: str, job_title: str, job_desc: str) -> Optional[Dict[str, Any]]:
    """
    Analyse un CV avec l'API Anthropic Claude
    Retourne un dictionnaire avec les résultats ou None en cas d'erreur
    """
    
    prompt = f"""Tu es un expert RH senior avec 20 ans d'expérience en recrutement. Analyse ce CV pour le poste suivant et réponds UNIQUEMENT en JSON valide, sans backticks, sans commentaires, sans markdown.

POSTE: {job_title}
{f'DESCRIPTION DU POSTE: {job_desc}' if job_desc else ''}

CV À ANALYSER:
{cv_text[:3000]}  # Limiter la taille pour éviter les dépassements

RÉPONDS EXACTEMENT AVEC CE FORMAT JSON (remplace les valeurs exemple par ton analyse):
{{
  "name": "Nom complet du candidat",
  "currentRole": "Poste actuel ou dernier poste occupé",
  "experience": "X ans",
  "education": "Diplôme principal et établissement",
  "location": "Ville/Pays si mentionné",
  "score": 75,
  "scores": {{
    "technical": 80,
    "experience": 70,
    "education": 75,
    "soft": 65
  }},
  "skills": [
    {{"name": "Python", "level": "expert"}},
    {{"name": "Management", "level": "intermédiaire"}}
  ],
  "verdict": "Résumé en 2-3 phrases de l'adéquation du candidat au poste",
  "strengths": ["Point fort 1", "Point fort 2", "Point fort 3"],
  "weaknesses": ["Point faible 1", "Point faible 2"],
  "tips": ["Conseil pratique 1 pour le recruteur", "Conseil pratique 2", "Conseil pratique 3"]
}}

RÈGLES:
- Les scores vont de 0 à 100
- Level des skills: "expert", "intermédiaire", ou "débutant"
- Sois objectif et constructif
- Réponds UNIQUEMENT avec le JSON, PAS DE TEXTE AUTOUR"""

    try:
        # Décommentez cette section si vous utilisez l'API Anthropic
        """
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = message.content[0].text
        clean_text = clean_json_response(text)
        result = json.loads(clean_text)
        """
        
        # Pour la démonstration sans API, générons un résultat simulé
        result = generate_mock_analysis(cv_text, job_title)
        
        # Validation basique des champs requis
        required_fields = ['name', 'score', 'verdict']
        for field in required_fields:
            if field not in result:
                result[field] = f"Information non disponible ({field})"
                if field == 'score':
                    result[field] = 50
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"Erreur de parsing JSON: {str(e)}")
        return None
    except Exception as e:
        print(f"Erreur d'analyse du CV: {str(e)}")
        return None


def generate_mock_analysis(cv_text: str, job_title: str) -> Dict[str, Any]:
    """
    Génère une analyse simulée pour la démonstration
    À remplacer par l'appel API réel
    """
    # Extraire un nom potentiel (simulation simple)
    lines = cv_text.strip().split('\n')
    potential_name = lines[0].strip() if lines else "Candidat Inconnu"
    
    # Simuler un score basé sur la longueur du CV et la présence de mots-clés
    base_score = min(85, len(cv_text) // 10)
    
    keywords = ['python', 'javascript', 'react', 'node', 'aws', 'docker', 'kubernetes', 
                'agile', 'scrum', 'management', 'leadership', 'machine learning', 'ai']
    
    keyword_score = 0
    for keyword in keywords:
        if keyword.lower() in cv_text.lower():
            keyword_score += 5
    
    final_score = min(95, base_score + keyword_score)
    
    return {
        "name": potential_name[:50],
        "currentRole": f"Candidat pour {job_title}",
        "experience": f"{max(1, len(cv_text) // 500)} ans",
        "education": "Master/Bac+5 (simulation)",
        "location": "France",
        "score": final_score,
        "scores": {
            "technical": min(90, final_score + 5),
            "experience": min(90, final_score - 5),
            "education": min(90, final_score + 10),
            "soft": min(90, final_score - 10)
        },
        "skills": [
            {"name": "Python", "level": "expert" if final_score > 70 else "intermédiaire"},
            {"name": "JavaScript", "level": "intermédiaire"},
            {"name": "SQL", "level": "expert" if final_score > 80 else "intermédiaire"},
            {"name": "Docker", "level": "intermédiaire"}
        ],
        "verdict": f"Candidat prometteur pour le poste de {job_title}. Le profil correspond aux exigences techniques avec une expérience solide dans le domaine. Recommandé pour un entretien approfondi.",
        "strengths": [
            "Excellente maîtrise technique",
            "Expérience pertinente dans le domaine",
            "Formation solide"
        ],
        "weaknesses": [
            "Pourrait améliorer ses compétences en leadership",
            "Expérience limitée en gestion de projet"
        ],
        "tips": [
            "Vérifier les réalisations concrètes lors de l'entretien",
            "Évaluer la capacité d'adaptation à la culture d'entreprise",
            "Demander des exemples de résolution de problèmes complexes"
        ]
    }


def generate_summary_ai(candidates: List[Dict], job_title: str) -> Optional[Dict[str, Any]]:
    """
    Génère un résumé global des candidats avec l'IA
    """
    
    if not candidates:
        return None
    
    candidates_info = ", ".join([
        f"{i+1}. {c.get('name', 'Inconnu')} ({c.get('score', 0)}/100)"
        for i, c in enumerate(candidates[:10])  # Limiter à 10 pour le prompt
    ])
    
    best_candidate = candidates[0] if candidates else {}
    
    prompt = f"""Tu es expert RH senior. Voici les résultats d'analyse de {len(candidates)} candidats pour le poste "{job_title}". Réponds UNIQUEMENT avec ce JSON (sans backticks ni markdown):

Candidats analysés (nom + score): {candidates_info}

RÉPONDS EXACTEMENT AVEC CE FORMAT:
{{
  "recommendation": "Analyse globale et recommandation en 3-4 phrases sur le profil des candidats",
  "bestMatch": "{best_candidate.get('name', 'Candidat 1')}",
  "keyInsight": "Une observation clé sur l'ensemble des candidatures reçues",
  "nextSteps": ["Action concrète 1 pour la suite du recrutement", "Action concrète 2", "Action concrète 3"]
}}"""

    try:
        # Décommentez cette section si vous utilisez l'API Anthropic
        """
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = message.content[0].text
        clean_text = clean_json_response(text)
        return json.loads(clean_text)
        """
        
        # Version simulée pour démonstration
        return {
            "recommendation": f"Parmi les {len(candidates)} candidats analysés pour le poste de {job_title}, le niveau global est satisfaisant. Le meilleur profil se démarque par ses compétences techniques et son expérience pertinente. Il est recommandé de contacter les 3 premiers candidats pour un entretien téléphonique dans les plus brefs délais.",
            "bestMatch": best_candidate.get('name', 'Candidat 1'),
            "keyInsight": f"Sur l'ensemble des candidatures, on observe une bonne maîtrise technique générale mais un manque de diversité dans les profils.",
            "nextSteps": [
                "Organiser des entretiens avec les 3 meilleurs candidats cette semaine",
                "Préparer des tests techniques pour évaluer les compétences pratiques",
                "Vérifier les références professionnelles des candidats présélectionnés"
            ]
        }
        
    except Exception as e:
        print(f"Erreur de génération du résumé: {str(e)}")
        return None


# ============================================================================
# ROUTES FLASK
# ============================================================================

@app.route('/')
def index():
    """Page d'accueil avec l'interface utilisateur"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/analyze', methods=['POST'])
def analyze_cvs():
    """
    Endpoint d'analyse des CVs
    Accepte: JSON avec jobTitle, jobDescription, cvTexts
    Retourne: JSON avec les résultats d'analyse
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
        
        job_title = data.get('jobTitle', '').strip()
        job_desc = data.get('jobDescription', '').strip()
        cv_texts = data.get('cvTexts', [])
        
        # Validation
        if not job_title:
            return jsonify({'error': 'Veuillez saisir le titre du poste'}), 400
        
        if not cv_texts or len(cv_texts) == 0:
            return jsonify({'error': 'Veuillez ajouter au moins un CV'}), 400
        
        # Analyser chaque CV
        candidates = []
        for i, cv_text in enumerate(cv_texts):
            try:
                result = analyze_cv_with_ai(cv_text, job_title, job_desc)
                
                if result and not result.get('error'):
                    candidates.append(result)
                else:
                    # Créer une entrée d'erreur pour ce CV
                    candidates.append({
                        'name': f'Candidat {i+1} (Erreur)',
                        'currentRole': 'Erreur d\'analyse',
                        'experience': 'N/A',
                        'education': 'N/A',
                        'location': 'N/A',
                        'score': 0,
                        'scores': {
                            'technical': 0,
                            'experience': 0,
                            'education': 0,
                            'soft': 0
                        },
                        'skills': [],
                        'verdict': 'Une erreur est survenue lors de l\'analyse de ce CV. Veuillez réessayer.',
                        'strengths': ['Information non disponible'],
                        'weaknesses': ['Information non disponible'],
                        'tips': ['Veuillez réanalyser ce CV manuellement']
                    })
            except Exception as e:
                print(f"Erreur CV {i+1}: {str(e)}")
                candidates.append({
                    'name': f'Candidat {i+1} (Erreur système)',
                    'score': 0,
                    'error': True
                })
        
        # Trier les candidats par score décroissant
        candidates.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Générer le résumé global
        summary = generate_summary_ai(candidates, job_title)
        
        return jsonify({
            'success': True,
            'candidates': candidates,
            'summary': summary,
            'jobTitle': job_title,
            'totalAnalyzed': len(candidates)
        })
        
    except Exception as e:
        print(f"Erreur serveur: {str(e)}")
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500


@app.route('/api/upload', methods=['POST'])
def upload_cv():
    """
    Endpoint d'upload de fichiers CV
    Accepte: Multipart form data avec 'files'
    Retourne: JSON avec les textes extraits
    """
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'Aucun fichier trouvé dans la requête'}), 400
        
        files = request.files.getlist('files')
        
        if not files or all(not f.filename for f in files):
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        
        cv_texts = []
        filenames = []
        errors = []
        
        for file in files:
            if file.filename:
                try:
                    # Lecture du contenu
                    content = file.read().decode('utf-8', errors='ignore')
                    
                    # Vérification basique du contenu
                    if len(content.strip()) < 50:
                        errors.append(f"{file.filename}: Fichier trop court (minimum 50 caractères)")
                        continue
                    
                    cv_texts.append(content)
                    filenames.append(file.filename)
                    
                except UnicodeDecodeError:
                    try:
                        # Essayer avec un autre encodage
                        file.seek(0)
                        content = file.read().decode('latin-1', errors='ignore')
                        cv_texts.append(content)
                        filenames.append(file.filename)
                    except Exception as e:
                        errors.append(f"{file.filename}: Erreur d'encodage - {str(e)}")
                except Exception as e:
                    errors.append(f"{file.filename}: Erreur de lecture - {str(e)}")
        
        if not cv_texts:
            return jsonify({
                'error': 'Aucun fichier valide n\'a pu être traité',
                'details': errors
            }), 400
        
        return jsonify({
            'success': True,
            'cvTexts': cv_texts,
            'filenames': filenames,
            'errors': errors if errors else None,
            'totalFiles': len(filenames)
        })
        
    except Exception as e:
        print(f"Erreur d'upload: {str(e)}")
        return jsonify({'error': f'Erreur d\'upload: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de vérification de santé"""
    return jsonify({
        'status': 'ok',
        'service': 'CV Analyser Pro',
        'version': '1.0.0',
        'timestamp': str(datetime.now()) if 'datetime' in dir() else 'OK'
    })


# ============================================================================
# TEMPLATE HTML (Interface Utilisateur Complète)
# ============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CV Analyser Pro - Analyse IA de CV</title>
    <style>
        :root {
            --bg: #0a0a0f;
            --surface: #13131a;
            --card: #1a1a24;
            --border: #2a2a3a;
            --accent: #6c5ce7;
            --accent-light: #a29bfe;
            --gold: #fdcb6e;
            --green: #00b894;
            --red: #d63031;
            --orange: #e17055;
            --text: #f0f0f8;
            --muted: #888899;
            --dim: #444455;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.5;
        }

        .container { max-width: 1100px; margin: 0 auto; padding: 24px 20px; }
        
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 20px;
        }

        .btn {
            background: var(--accent);
            border: none;
            border-radius: 10px;
            color: #fff;
            cursor: pointer;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s;
        }

        .btn:hover { opacity: 0.9; transform: translateY(-1px); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

        .btn-primary {
            width: 100%;
            background: linear-gradient(135deg, var(--accent), var(--accent-light));
            padding: 16px;
            font-size: 16px;
            font-weight: 700;
        }

        input, textarea {
            width: 100%;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px 16px;
            color: var(--text);
            font-size: 14px;
            outline: none;
            font-family: inherit;
            transition: border-color 0.2s;
            box-sizing: border-box;
        }

        input:focus, textarea:focus { border-color: var(--accent); }
        textarea { min-height: 120px; }

        .section-title {
            font-size: 12px;
            color: var(--accent-light);
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 16px;
            font-weight: 600;
        }

        .upload-zone {
            border: 2px dashed var(--border);
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            background: transparent;
        }

        .upload-zone:hover {
            border-color: var(--accent);
            background: rgba(108, 92, 231, 0.05);
        }

        .file-item {
            display: flex;
            align-items: center;
            gap: 12px;
            background: var(--surface);
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 8px;
            transition: all 0.2s;
        }

        .file-item:hover { background: var(--border); }

        .candidate-card {
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 16px;
            border-radius: 14px;
            position: relative;
            margin-bottom: 10px;
        }

        .candidate-card:hover { transform: translateX(4px); }

        .score-badge {
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            padding: 6px 14px;
            border-radius: 12px;
            border: 2px solid;
            min-width: 60px;
        }

        .result-layout {
            display: grid;
            grid-template-columns: 340px 1fr;
            gap: 20px;
            align-items: start;
        }

        @media (max-width: 768px) {
            .result-layout { grid-template-columns: 1fr; }
        }

        .loader {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 80vh;
            gap: 24px;
        }

        .spinner {
            font-size: 48px;
            animation: spin 2s linear infinite;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .hidden { display: none !important; }

        .error-message {
            background: rgba(214, 48, 49, 0.08);
            border: 1px solid rgba(214, 48, 49, 0.25);
            border-radius: 10px;
            padding: 12px 16px;
            color: var(--red);
            font-size: 14px;
            margin-bottom: 16px;
        }

        .skill-tag {
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            border: 1px solid;
        }

        .progress-bar {
            flex: 1;
            background: rgba(68, 68, 85, 0.27);
            border-radius: 4px;
            height: 6px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 1s ease-out;
        }

        .initials-circle {
            width: 46px;
            height: 46px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: 700;
            flex-shrink: 0;
        }

        .grade-label {
            font-size: 12px;
            color: var(--muted);
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 16px;
        }
    </style>
</head>
<body>
    <!-- Page de configuration -->
    <div id="setup-page" class="container" style="max-width: 680px; padding-top: 48px;">
        <div style="text-align: center; margin-bottom: 48px;">
            <div style="font-size: 48px; margin-bottom: 16px;">🧠</div>
            <h1 style="font-size: 32px; font-weight: 800; margin-bottom: 8px; background: linear-gradient(135deg, var(--accent-light), var(--gold)); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                CV Analyser Pro
            </h1>
            <p style="color: var(--muted); font-size: 15px;">
                Analysez des CV par intelligence artificielle et trouvez le meilleur candidat
            </p>
        </div>

        <div class="card">
            <div class="section-title">📋 1. Définir le poste</div>
            <input type="text" id="jobTitle" placeholder="Ex: Développeur Full Stack Senior, Chef de projet..."
                   style="margin-bottom: 14px;">
            <textarea id="jobDescription" placeholder="Description du poste, compétences requises, années d'expérience... (optionnel mais recommandé)"></textarea>
        </div>

        <div class="card">
            <div class="section-title">📄 2. Charger les CV</div>
            <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
                <div style="font-size: 48px; margin-bottom: 12px;">📁</div>
                <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;" id="uploadText">
                    Glisser-déposer vos CV ou cliquer pour sélectionner
                </div>
                <div style="color: var(--muted); font-size: 13px;">
                    Formats acceptés: .txt, .md, .pdf, .doc, .docx
                </div>
            </div>
            <input type="file" id="fileInput" multiple accept=".txt,.md,.pdf,.doc,.docx" style="display: none;">
            <div id="fileList" style="margin-top: 16px;"></div>
        </div>

        <div id="errorMessage" class="error-message hidden"></div>

        <button id="analyzeBtn" class="btn btn-primary" onclick="analyzeCVs()">
            🚀 Analyser les CV
        </button>

        <div style="text-align: center; margin-top: 24px; color: var(--dim); font-size: 12px;">
            Propulsé par Claude (Anthropic) · Traitement local sécurisé
        </div>
    </div>

    <!-- Page de chargement -->
    <div id="loading-page" class="loader hidden">
        <div class="spinner">⚙️</div>
        <div style="font-size: 24px; font-weight: 700;">Analyse IA en cours...</div>
        <div style="color: var(--muted); font-size: 16px;" id="loadingMessage">
            Préparation de l'analyse...
        </div>
        <div style="width: 300px; height: 4px; background: var(--border); border-radius: 2px; overflow: hidden;">
            <div style="width: 60%; height: 100%; background: var(--accent); border-radius: 2px; animation: loading 1.5s ease-in-out infinite;"></div>
        </div>
        @keyframes loading {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(200%); }
        }
    </div>

    <!-- Page de résultats -->
    <div id="results-page" class="container hidden">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 32px;">
            <div>
                <div class="grade-label">Résultats d'analyse</div>
                <div style="font-size: 28px; font-weight: 700; color: var(--text);" id="resultJobTitle"></div>
                <div style="color: var(--muted); font-size: 14px; margin-top: 4px;" id="candidateCount"></div>
            </div>
            <button class="btn" onclick="newAnalysis()" style="background: var(--accent);">
                + Nouvelle analyse
            </button>
        </div>

        <div id="summaryCard" class="card hidden" style="border-color: var(--accent); border-width: 2px;"></div>

        <div class="result-layout">
            <div id="candidatesList"></div>
            <div id="detailPanel"></div>
        </div>
    </div>

    <script>
        // État de l'application
        let uploadedFiles = [];
        let cvTexts = [];
        let currentCandidates = [];
        let selectedCandidate = null;

        // Configuration des grades
        const GRADE_CONFIG = {
            A: { color: '#00b894', label: 'Excellent', emoji: '★★★★★' },
            B: { color: '#a29bfe', label: 'Très bien', emoji: '★★★★☆' },
            C: { color: '#fdcb6e', label: 'Bien', emoji: '★★★☆☆' },
            D: { color: '#e17055', label: 'Passable', emoji: '★★☆☆☆' },
            F: { color: '#d63031', label: 'Insuffisant', emoji: '★☆☆☆☆' }
        };

        function getGradeConfig(score) {
            if (score >= 85) return GRADE_CONFIG.A;
            if (score >= 70) return GRADE_CONFIG.B;
            if (score >= 55) return GRADE_CONFIG.C;
            if (score >= 40) return GRADE_CONFIG.D;
            return GRADE_CONFIG.F;
        }

        // Gestion de l'upload par drag & drop
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = 'var(--accent)';
            uploadZone.style.background = 'rgba(108, 92, 231, 0.08)';
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.style.borderColor = 'var(--border)';
            uploadZone.style.background = 'transparent';
        });

        uploadZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = 'var(--border)';
            uploadZone.style.background = 'transparent';
            await handleFiles(e.dataTransfer.files);
        });

        fileInput.addEventListener('change', async (e) => {
            await handleFiles(e.target.files);
            fileInput.value = ''; // Réinitialiser pour permettre la resélection
        });

        async function handleFiles(files) {
            if (!files || files.length === 0) return;

            const formData = new FormData();
            const newFiles = [];

            for (let file of files) {
                // Vérifier si le fichier existe déjà
                const exists = uploadedFiles.some(f => f.name === file.name && f.size === file.size);
                if (!exists) {
                    formData.append('files', file);
                    newFiles.push(file);
                }
            }

            if (newFiles.length === 0) {
                showError('Ces fichiers ont déjà été ajoutés.');
                return;
            }

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    uploadedFiles = [...uploadedFiles, ...newFiles];
                    cvTexts = [...cvTexts, ...data.cvTexts];
                    updateFileList();
                    
                    if (data.errors && data.errors.length > 0) {
                        showError('Certains fichiers n\'ont pas pu être traités: ' + data.errors.join(', '));
                    }
                } else {
                    showError(data.error || 'Erreur lors de l\'upload');
                }
            } catch (error) {
                console.error('Erreur upload:', error);
                showError('Erreur de connexion lors de l\'upload');
            }
        }

        function updateFileList() {
            const fileList = document.getElementById('fileList');
            const uploadText = document.getElementById('uploadText');
            
            if (uploadedFiles.length === 0) {
                fileList.innerHTML = '';
                uploadText.textContent = 'Glisser-déposer vos CV ou cliquer pour sélectionner';
                return;
            }

            uploadText.textContent = `${uploadedFiles.length} CV chargé${uploadedFiles.length > 1 ? 's' : ''}`;
            
            fileList.innerHTML = uploadedFiles.map((file, index) => `
                <div class="file-item">
                    <span style="font-size: 20px;">📄</span>
                    <span style="flex: 1; font-size: 13px; color: var(--text);">${escapeHtml(file.name)}</span>
                    <span style="font-size: 11px; color: var(--muted);">${(file.size / 1024).toFixed(1)} KB</span>
                    <button onclick="removeFile(${index})" style="background: none; border: none; color: var(--dim); cursor: pointer; font-size: 18px; padding: 4px 8px; border-radius: 4px;" title="Supprimer ce CV">
                        ✕
                    </button>
                </div>
            `).join('');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function removeFile(index) {
            uploadedFiles.splice(index, 1);
            cvTexts.splice(index, 1);
            updateFileList();
        }

        function showPage(pageId) {
            ['setup-page', 'loading-page', 'results-page'].forEach(id => {
                document.getElementById(id).classList.add('hidden');
            });
            document.getElementById(pageId).classList.remove('hidden');
        }

        function showError(message) {
            const errorEl = document.getElementById('errorMessage');
            errorEl.textContent = '⚠️ ' + message;
            errorEl.classList.remove('hidden');
            setTimeout(() => errorEl.classList.add('hidden'), 5000);
        }

        async function analyzeCVs() {
            const jobTitle = document.getElementById('