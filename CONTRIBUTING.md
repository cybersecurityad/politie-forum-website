# 🤝 Contributing to Politie Forum Nederland

Welkom bij Politie Forum Nederland! We waarderen je interesse in het bijdragen aan dit project. Dit document bevat richtlijnen voor het bijdragen aan de codebase, rapporten van problemen en suggesties voor nieuwe features.

## 📋 Inhoudsopgave
- [Code van Gedrag](#code-van-gedrag)
- [Hoe Bijdragen](#hoe-bijdragen)
- [Ontwikkelomgeving Opzetten](#ontwikkelomgeving-opzetten)
- [Stijlrichtlijnen](#stijlrichtlijnen)
- [Pull Request Proces](#pull-request-proces)
- [Problemen Rapporteren](#problemen-rapporteren)
- [Feature Verzoeken](#feature-verzoeken)

## 🤝 Code van Gedrag

Dit project volgt een code van gedrag om een open en welkome omgeving te bevorderen. Door bij te dragen aan dit project, ga je akkoord met:

- **Respectvol zijn** tegenover alle deelnemers
- **Constructieve communicatie** gebruiken
- **Inclusiviteit** bevorderen
- **Professioneel gedrag** handhaven
- **Privacy respecteren** van alle gebruikers

## 🚀 Hoe Bijdragen

### 1. Fork het Project
```bash
git clone https://github.com/your-username/politie-forum-nl.git
cd politie-forum-nl
git checkout -b feature/AmazingFeature
```

### 2. Maak je Wijzigingen
- Volg de [stijlrichtlijnen](#stijlrichtlijnen)
- Test je wijzigingen grondig
- Zorg voor backwards compatibility
- Update documentatie indien nodig

### 3. Commit je Wijzigingen
```bash
git add .
git commit -m "Add: Beschrijving van de feature"
```

### 4. Push naar GitHub
```bash
git push origin feature/AmazingFeature
```

### 5. Open een Pull Request
- Gebruik de Pull Request template
- Beschrijf duidelijk wat je hebt gewijzigd
- Link naar gerelateerde issues indien van toepassing

## 🛠️ Ontwikkelomgeving Opzetten

### Vereisten
- Node.js 16+ ([Download](https://nodejs.org/))
- Firebase CLI (`npm install -g firebase-tools`)
- Git ([Download](https://git-scm.com/))

### Installatie Stappen
```bash
# 1. Clone de repository
git clone https://github.com/your-username/politie-forum-nl.git
cd politie-forum-nl

# 2. Installeer dependencies
npm install

# 3. Login bij Firebase
firebase login

# 4. Configureer Firebase project
firebase use --add

# 5. Start lokale development server
firebase serve
```

### Database Setup
```bash
# Open database seeder in browser
open public/database-seeder.html

# Of gebruik de command line
firebase database:set /forum/categories -d '{"algemeen": {}}'
```

## 📝 Stijlrichtlijnen

### HTML/CSS
- Gebruik semantische HTML5 elementen
- Volg BEM methodologie voor CSS classes
- Gebruik CSS Grid/Flexbox voor layouts
- Minimaliseer CSS nesting (max 3 levels)
- Gebruik CSS custom properties voor theming

### JavaScript
- Gebruik ES6+ features (arrow functions, template literals, etc.)
- Gebruik async/await voor promises
- Implementeer error handling
- Comment complex logic
- Gebruik descriptive variable names

### Bestanden Organisatie
```
public/
├── components/     # Herbruikbare componenten
├── styles/        # CSS bestanden
├── scripts/       # JavaScript modules
├── images/        # Afbeeldingen en iconen
└── pages/         # HTML pagina's
```

### Commit Berichten
Gebruik de volgende format voor commit berichten:
```
Type: Beschrijving van de wijziging

[Optionele body met details]
```

**Types:**
- `Add:` Nieuwe features
- `Fix:` Bug fixes
- `Update:` Verbeteringen aan bestaande code
- `Remove:` Verwijderde features
- `Docs:` Documentatie updates
- `Style:` Code styling zonder functionele wijzigingen

### Voorbeelden:
```
Add: User authentication system
Fix: Mobile navigation menu not closing
Update: Improve loading performance
Docs: Add API documentation
```

## 🔄 Pull Request Proces

### PR Template
Gebruik deze template voor Pull Requests:

```markdown
## Beschrijving
[Wat heb je gewijzigd en waarom?]

## Type van Wijziging
- [ ] 🐛 Bug fix
- [ ] ✨ Nieuwe feature
- [ ] 💥 Breaking change
- [ ] 📚 Documentatie
- [ ] 🎨 Styling
- [ ] 🔧 Refactoring

## Checklist
- [ ] Mijn code volgt de bestaande stijlrichtlijnen
- [ ] Ik heb mijn eigen code getest
- [ ] Ik heb relevante documentatie bijgewerkt
- [ ] Mijn wijzigingen werken backwards compatible
- [ ] Ik heb nieuwe dependencies toegevoegd aan package.json

## Screenshots (indien van toepassing)
[Voeg screenshots toe van je wijzigingen]

## Gerelateerde Issues
[Link naar gerelateerde issues, bijv. #123]
```

### Review Proces
1. **Automated Checks:** CI/CD pipeline controleert code kwaliteit
2. **Peer Review:** Minimaal 1 reviewer bekijkt de code
3. **Testing:** Reviewer test de functionaliteit
4. **Approval:** PR wordt goedgekeurd of feedback gegeven
5. **Merge:** PR wordt gemerged naar main branch

## 🐛 Problemen Rapporteren

### Bug Reports
Gebruik de bug report template:

```markdown
**Beschrijving van het probleem**
[Wat gebeurt er? Wat verwachtte je?]

**Stappen om te reproduceren**
1. Ga naar '...'
2. Klik op '...'
3. Scroll naar '...'
4. Zie fout

**Verwachte gedrag**
[Wat zou er moeten gebeuren?]

**Screenshots**
[Voeg screenshots toe]

**Omgeving**
- OS: [bijv. Windows 10]
- Browser: [bijv. Chrome 91]
- Device: [bijv. Desktop/Mobile]

**Extra informatie**
[Eventuele extra context]
```

### Feature Verzoeken
Voor nieuwe features:

```markdown
**Feature Beschrijving**
[Wat wil je toevoegen?]

**Probleem dat het oplost**
[Waarom is dit nuttig?]

**Voorgestelde oplossing**
[Hoe zou het moeten werken?]

**Alternatieven**
[Andere oplossingen die je hebt overwogen?]

**Extra context**
[Screenshots, mockups, etc.]
```

## 🎯 Development Doelen

### Prioriteiten
1. **Toegankelijkheid** - WCAG 2.1 AA compliance
2. **Performance** - Core Web Vitals optimalisatie
3. **SEO** - Uitstekende zoekmachine vindbaarheid
4. **Gebruiksvriendelijkheid** - Intuïtieve user experience
5. **Beveiliging** - GDPR compliance en security best practices

### Coding Standards
- **Accessibility:** Alt tekst voor alle afbeeldingen
- **Performance:** Lazy loading voor images
- **SEO:** Semantische HTML structuur
- **Security:** Input validatie en sanitization
- **Testing:** Unit tests voor kritische functies

## 📞 Contact

Voor vragen over bijdragen:
- **GitHub Issues:** [https://github.com/your-username/politie-forum-nl/issues](https://github.com/your-username/politie-forum-nl/issues)
- **Discussions:** [https://github.com/your-username/politie-forum-nl/discussions](https://github.com/your-username/politie-forum-nl/discussions)
- **Email:** contributions@politie-forum.nl

## 🙏 Dankwoord

Bedankt voor je bijdrage aan Politie Forum Nederland! Samen maken we Nederland veiliger door betere communicatie tussen burgers en politie.

---

**🇳🇱 Politie Forum Nederland - Samen Sterker 🇳🇱**