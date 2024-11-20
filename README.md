
# Discord Logger

Discord Logger est un bot open-source conçu pour enregistrer méticuleusement les messages et les événements dans Discord sans la lourdeur d'un bot tout-en-un. Ecrit en python en utilisant la bibliothèque discord.py, ce bot est facile à configurer et peut enregistrer plusieurs serveurs. Codé pour être utilisé avec ou sans base de données mongodb.

📝 **A propos** :
Discord Logger est en début de développement et vous est présenté par kipperz. Il a été fork par [clockwork64](https://github.com/clockwork04/discord-logger), son profil disponible [ici](https://github.com/clockwork04). Sur les dernières versions du repo officiel, de nombreux bugs sont apparus. J'ai donc pris ce fork, mais pareil il n'était pas à jour car le code était basé sur le faite qu'il y ait obligatoirement mongo de relié pour pouvoir fonctionner. J'ai donc cherché dans les commits, puis j'ai trouvé [ça](https://github.com/kipperz/discord-logger/commit/b307d898425d65a464e9615d9f5d8cd4e0d30a1d).
J'ai donc rajouté ces lignes de code, et bingo ça a marché. A l'aide de copilot j'ai pu résoudre quelques bugs, et le bot est fonctionnel. Alors oui il y a encore pleins d'erreurs dans les logs, que je ne suis pas en mesure de corriger, mais libre à vous de contribuer. Les erreurs dans les logs n'empêchent pas de faire marcher le bot.

## Fonctionnalités

- Enregistrement des actions du modérateur** : Gardez une trace de toutes les actions prises par les modérateurs du serveur, ce qui permet de rendre des comptes et d'assurer la traçabilité.

- Sauvegarde du journal d'audit** : Ne perdez pas les journaux d'audit de votre serveur. Discord conserve votre journal d'audit pendant seulement 90 jours, mais avec Discord Logger, vous pouvez les sauvegarder dans un canal texte désigné et/ou une base de données.

- **Suivi des membres** :
  - **Join/Part Logging** : Surveillez quand les membres rejoignent ou quittent le serveur.
  - Suivi des invitations** : Enregistre l'invitation utilisée avec le message d'adhésion du membre.
  - Enregistrement des actions** : Enregistre les changements de nom d'utilisateur et de pseudo pour garder une trace de l'identité des membres.

- Enregistrement des messages** :
  - **Enregistrement dans une base de données** : Conservez tous les messages dans une base de données dédiée, afin de ne jamais perdre d'informations importantes.
  - Suivi des modifications et des suppressions** : Capturez les modifications et les suppressions afin de préserver l'intégrité des communications du serveur. Exploitez la base de données lorsque les données des messages ne sont pas mises en cache.

- Journaux des conversations vocales** : Obtenez des informations sur l'utilisation du chat vocal, en comprenant les modèles, les durées et la participation.

## Auto-hébergement

Actuellement, votre option pour utiliser Discord Logger est l'auto-hébergement. Le bot est conçu avec un support multi-serveur, ce qui le rend polyvalent pour des communautés de différentes tailles.

### Installation et configuration

1. Clonez ce dépôt :
   ```
   git clone https://github.com/Stosbaby/Bot-log-discord-python.git
   ```

2. Naviguez vers le répertoire du dépôt et installez les dépendances nécessaires. (avec le requirements.txt, ```pip install discord.py```, par ex)

3. Modifiez config/settings.py

4. Modifier config/guild_settings.json (ne pas toucher à guild_settings.json)

5. Lancez le bot :
   ```
   python main.py
   ```

## Support & Contribution

Pour du support, des demandes de fonctionnalités ou des contributions, veuillez ouvrir un problème sur ce dépôt.
