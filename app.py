from flask import Flask, request 
from flask_session import Session
from flask_cors import CORS
import openai 
import os
import uuid
from datetime import datetime, timedelta
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, jsonify
import mysql.connector
from flask import render_template

app = Flask(__name__) 
CORS(app)
openai.api_key = open("key.txt","r").read().strip('\n')

# Fonction pour ajouter une demande à la base de données
def ajouter_DEMANDE(utilisateur, DEMANDE , phone_number):
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='chatbot_db'      
    )               
    cursor = conn.cursor() 
    cursor.execute('INSERT INTO DEMANDE (incoming_msg, response_msg, phone_number) VALUES (%s, %s, %s)', (utilisateur, DEMANDE , phone_number))
    conn.commit()
    cursor.close()
    conn.close() 
    
# Définir la durée d'expiration (par exemple, 5 minutes)
EXPIRATION_DUREE = timedelta(minutes=60)
def session_expiree(last_interaction):
    # Obtenir l'heure actuelle
    maintenant = datetime.now()
     # Calculer la différence entre maintenant et la dernière interaction
    difference = maintenant - last_interaction
    # Retourner True si la session a expiré
    return difference > EXPIRATION_DUREE
    
# Fonction pour marquer l'utilisateur comme ayant été transféré
def marquer_comme_transfere(phone_number):
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='123456789',
        database='chatbot_db'
    )
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE DEMANDE SET has_been_transferred = TRUE WHERE phone_number = %s ORDER BY id DESC LIMIT 1',
        (phone_number,)
    )
    conn.commit()
    cursor.close()
    conn.close()


# Fonction pour marquer un utilisateur comme étant avec un agent humain
def marquer_avec_agent(phone_number):
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='123456789',
        database='chatbot_db'
    )
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE DEMANDE SET is_with_agent = TRUE WHERE phone_number = %s ORDER BY id DESC LIMIT 1',
        (phone_number,)
    )
    conn.commit()
    cursor.close()
    conn.close() 
    
# Fonction pour interroger le chatbot IA
    
def interroger_chatbot(DEMANDE):
    response = openai.Completion.create(
        engine="MyISAM",
        prompt=DEMANDE,
        max_tokens=150
    )
    return response.choices[0].text.strip()

def CustomChatGPT(user_input: str):
    messages.append({"role": "user", "content": user_input})
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = messages 
    ) 
    ChatGPT_reply = response["choices"][0]["message"]["content"]    
    return ChatGPT_reply

messages = [
    {"role":"system", "content": "Tu es un expert en service client ,tu repondras aux clients selon la langue utilisée, tu resteras dans le contexte de FanBusy ,tu repondras aux questions qui sont liées à FanBusy. Si tu ne possèdes pas de réponse aux questions tu devras t'excuser auprès du client en lui disant que tu es désolé mais tu n'as pas d'element de réponse. Et si tu reçois des questions qui n'ont aucun rapport avec FanBusy tu diras aux clients que tu ne peux malheureusement pas répondre car tu es un assistant virtuel de fanbusy et tu ne possèdes que des informations concernant FanBusy.En tant que expert en service client pour une entreprise digitale, lors d'une conversation avec un utilisateur qui souhaite s'abonner à un créateur de contenu sur FanBusy ou qui voudrais juste des informations sur FanBusy , FanBusy  est une plateforme innovante qui résout le problème de monétisation du contenu pour les créateurs africains. Elle permet aux écrivains, artistes, musiciens et influenceurs de transformer leur passion en source de revenus. Sur FanBusy, les créateurs proposent un contenu exclusif à leurs abonnés via des abonnements mensuels, des chats privés et des demandes personnalisées. Cela offre aux utilisateurs un accès exclusif à du contenu de qualité tout en soutenant directement leurs créateurs préférés , tu prendra en compte les etapes suivante pour mieux aider les clients Recherchez le Créateur : Utilisez la page de recherche (icône 🔍) pour découvrir les créateurs inscrits sur FanBusy. Parcourez les profils et trouvez celui qui vous intéresse. Visitez le Profil du Créateur :Rendez-vous sur le profil du créateur que vous souhaitez suivre.Cliquez sur S'abonner:Sur le profil du créateur, cliquez sur le bouton S'abonner. Vous serez automatiquement abonné et aurez accès au contenu exclusif.Explorez les Avantages de Votre Abonnement :Profitez des avantages offerts par votre abonnement, tels que la visualisation du contenu flouté, l'achat de MOD, et la possibilité d'échanger avec le créateur via le chat.N'oubliez pas que les abonnements sont renouvelables automatiquement et sans engagement. Vous pouvez interrompre le renouvellement automatique à tout moment avant la date d'anniversaire de l'achat"},
    {"role":"system","content":"Tu dois analyser les questions qui te sont posées afin de trouver les préoccupations des utilisateurs , tu devras discuter de façon simple avec les utilisateurs .Tu dois éviter les rédondances dans tes réponses "},
]
 
# Fonction pour vérifier si l'utilisateur est insatisfait
def est_insatisfait(user_input: str):
    insatisfaction_keywords = ["je ne suis pas satisfait", "pas content", "je suis mécontent", "ce n'est pas ce que je voulais","non", "je ne suis pas satisfait"]
    for keyword in insatisfaction_keywords:
        if keyword.lower() in user_input.lower():
            return True
    return False

# Connexion à la base de données
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='chatbot_db'
    ) 

      
# Charger la session utilisateur
def charger_session(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM session WHERE user_id = %s ORDER BY last_interaction DESC LIMIT 1', (user_id,))
    session_data = cursor.fetchone()

    if not session_data:
        # Si la session n'existe pas, en créer une nouvelle
        session_data = {
            "session_id":str(uuid.uuid4()),
            'user_id': user_id,
            'request_count': 0,
            'with_agent': False,
            'last_interaction': datetime.now()
        }
        cursor.execute('INSERT INTO session (session_id,user_id,request_count,with_agent,last_interaction) VALUES (%s,%s,%s,%s,%s)', (str(uuid.uuid4()),user_id,0,False,session_data['last_interaction']))
        conn.commit()
    else:
        # Vérifier si la session a expiré
        last_interaction = session_data['last_interaction']
        if session_expiree(last_interaction):
            session_data = {
                "session_id":str(uuid.uuid4()),
                'user_id': user_id,
                'request_count': 0,
                'with_agent': False,
                'last_interaction': datetime.now()
            }
            cursor.execute('INSERT INTO session (session_id,user_id,request_count,with_agent,last_interaction) VALUES (%s,%s,%s,%s,%s)', (str(uuid.uuid4()),user_id,0,False,session_data['last_interaction']))
            conn.commit()
            
    cursor.close()
    conn.close()
    return session_data 
# Sauvegarder les informations de la session
def sauvegarder_session(session_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE session 
        SET request_count = %s, with_agent = %s, last_interaction =CURRENT_TIMESTAMP
        WHERE session_id = %s
    ''', (session_data['request_count'], session_data['with_agent'], session_data['session_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    # Fonction pour obtenir la liste des sessions actives et en attente d'un agent humain
def obtenir_sessions_en_attente():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Récupérer les sessions actives où l'utilisateur n'est pas encore avec un agent
    query = '''
    SELECT * FROM session 
    WHERE with_agent = FALSE AND TIMESTAMPDIFF(MINUTE, last_interaction, NOW()) <= %s
    '''
    cursor.execute(query, (EXPIRATION_DUREE.total_seconds() / 60,))
    sessions_en_attente = cursor.fetchall()
    cursor.close()
    conn.close()
    return sessions_en_attente
@app.route("/sessions_en_attente", methods=['POST'])
def lister_sessions_en_attente():
    sessions = obtenir_sessions_en_attente()
    return jsonify(sessions), 200

# Fonction pour obtenir la liste des sessions actives avec un agent humain
def obtenir_sessions_avec_agent():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = '''
    SELECT * FROM session 
    WHERE with_agent = TRUE
    '''
    cursor.execute(query)
    sessions_avec_agent = cursor.fetchall()
    cursor.close()
    conn.close()
    print(sessions_avec_agent) 
    return sessions_avec_agent
@app.route("/sessions_avec_agent", methods=['GET'])
def lister_sessions_avec_agent():
    sessions = obtenir_sessions_avec_agent()
    return jsonify(sessions),200 



@app.route("/", methods=['POST'])
def recevoir_DEMANDE():
    data = request.json
    utilisateur = data.get('utilisateur')
    DEMANDE = data.get('DEMANDE')
    
# Ajouter la demande et la réponse à la base de données
    ajouter_DEMANDE(utilisateur, DEMANDE)
    
    return jsonify({"message": "Demande reçue avec succès", "reponse": "success"}), 200

@app.route("/demande", methods=['POST'])
def whatsapp_reply():
    print(request)
    incoming_msg = request.values.get('Body', '').strip()
    phone_number = request.values.get('From', '')
    response = MessagingResponse()
    message = response.message() 
    
    # Charger la session
    session_data = charger_session(phone_number)
    # Vérifier si l'utilisateur est déjà avec un agent humain
    if session_data['with_agent']:
      return jsonify({"message": "Vous êtes déjà en conversation avec un agent humain. Merci de patienter."}), 200
    # Incrémenter le compteur de requêtes
    session_data['request_count'] += 1
    # Si le nombre de requêtes dépasse un certain seuil, transférer à un agent humain
    if session_data['request_count'] >=10:
        session_data['with_agent'] = True
        message.body("Vous avez posé plusieurs questions. Je vais maintenant vous transférer à un agent humain qui pourra vous aider davantage.")
        sauvegarder_session(session_data)
        
        return str(response)   
    
    resp = CustomChatGPT(incoming_msg) 
    ajouter_DEMANDE(incoming_msg ,resp, phone_number)
    sauvegarder_session(session_data)  

    message.body(resp)   
    return str(response)
if __name__ == "__main__":
    app.run() 
    