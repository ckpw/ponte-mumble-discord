import base64
from datetime import timedelta
from PIL import Image
from io import BytesIO
import html2text
import pymumble_py3 as pymumble
import asyncio
from urllib.parse import unquote
from bs4 import BeautifulSoup
import markdown
acao_pendente = False
# Configure aqui
canal = 109395158109395158
endereco_ip = "127.0.0.1"
porta = 64738
# Criar uma instância da classe Mumble
bot = pymumble.Mumble(
    endereco_ip,
    "bot",
    port=porta,
    certfile="/cert.pem",
    keyfile="/key.pem",
    reconnect=True,
)
bot.set_loop_rate(0.05)
# Conectar ao servidor
bot.start()
bot.is_ready()
canal_bot_privado = bot.channels.find_by_name("Privado")
canais_privados = {}
autor_mensagem = False
nome_canal = False
usuarios_permitidos = ["bot"]

def mensagem_recebida(msg):
    global autor_mensagem
    global nome_canal
    print(msg)
    autor_mensagem = bot.users[msg.actor]
    if msg.message.startswith("/") and msg.channel_id:
        autor_mensagem.send_text_message(
            f"Ei! Você só pode enviar comandos mandando mensagem no privado. Para fazer isso, clique 2 vezes no meu usuário."
        )
    elif msg.message.startswith("/ajuda"):
        autor_mensagem\
            .send_text_message("<p>Estes são alguns dos comandos disponíveis do nosso bot:</p>"
                               "<ul> "
                               "<li>/ajuda - exibe a lista de comandos disponíveis do bot.</li>"
                               "<li>/criar (nome) (senha) - cria um novo canal de voz privado com"
                               " o nome especificado e uma senha para acesso."
                               "</li>"
                               "<li>/mover (nome) (senha) - move você para o canal privado de voz "
                               "com o nome especificado, usando a senha fornecida para acesso.</li>"
                               "<li>/denunciar (usuário) (motivo) - denuncia um usuário com o motivo "
                               "especificado.</li>"
                               "<li>/dc - enviar uma mensagem para o Discord. Esse comando só está "
                               "disponível para certos usuários que tem acesso ao canal Discord.</li>"
                               "</ul>")
    elif msg.message.startswith("/dc") and autor_mensagem["name"] in usuarios_permitidos:
        input = msg.message[len("/dc") :].strip()
        mensagem = f"**{autor_mensagem['name']}**\u3164{input}"
        try:
            msg = asyncio.run_coroutine_threadsafe(
                async_mensagem(mensagem), client.loop
            )
        except Exception as e:
            print(e)
    elif msg.message.startswith("/criar"):
        input = msg.message[len("/criar"):].strip()
        try:
            nome_canal, senha = input.split(maxsplit=1)
        except ValueError:
            autor_mensagem.send_text_message(
                "Formato inválido. O comando /criar deve ser seguido pelo nome do canal e uma senha."
            )
            return
        if nome_canal in canais_privados.keys():
            autor_mensagem.send_text_message(
                f"O canal {nome_canal} já existe. Use o comando /mover para entrar no canal."
            )
            return
        canal_privado = bot.channels.new_channel(
            canal_bot_privado['channel_id'],
            name=nome_canal, temporary=True
        )
        canais_privados[nome_canal] = senha
        global acao_pendente
        acao_pendente = 9
    elif msg.message.startswith("/mover"):
        input = msg.message[len("/mover"):].strip()
        try:
            nome_canal, senha = input.split(maxsplit=1)
        except ValueError:
            autor_mensagem.send_text_message(
                "Formato inválido. O comando /mover deve ser seguido pelo nome do canal e sua senha."
            )
            return
        if nome_canal in canais_privados and canais_privados[nome_canal] == senha:
            bot.channels.find_by_name(nome_canal).move_in(autor_mensagem['session'])
        else:
            autor_mensagem.send_text_message("Canal privado ou senha inválidos.")
    elif msg.message.startswith("/denunciar"):
        input = msg.message[len("/denunciar"):].strip()
        try:
            usuario, motivo = input.split(maxsplit=1)
        except ValueError:
            autor_mensagem.send_text_message(
                "Formato inválido. O comando /denunciar deve ser "
                "seguido pelo nome do usuário e o motivo da denúncia."
            )
            return
        usuario_mumble = encontrar_usuario_por_nome(usuario)
        if not usuario_mumble:
            autor_mensagem.send_text_message(
                f"O usuário {usuario} não existe."
            )
            return
        usuario_mumble.send_text_message("Cuidado aí, alguém acabou de te denunciar.")
        mensagem = f"\U0001F6A8 **{autor_mensagem['name']}** denunciou **{usuario}** por _{motivo}_"

        try:
            msg = asyncio.run_coroutine_threadsafe(
                async_mensagem(mensagem), client.loop
            )
        except Exception as e:
            print(e)
        autor_mensagem.send_text_message(
            f"Obrigado por denunciar {usuario}. Os moderadores serão notificados."
        )
    elif autor_mensagem["name"] in usuarios_permitidos:
        mensagem = f"**{autor_mensagem['name']}**\u3164{msg.message}"
        try:
            msg = asyncio.run_coroutine_threadsafe(
                async_mensagem(mensagem), client.loop
            )
        except Exception as e:
            print(e)



def conectado(user):
    try:
        msg = asyncio.run_coroutine_threadsafe(async_conectado(user), client.loop)
    except Exception as e:
        print(e)


def movido(session, actor):
    try:
        msg = asyncio.run_coroutine_threadsafe(
            async_movido(session, actor), client.loop
        )
    except Exception as e:
        print(e)


def enviar_mensagem(mensagem):
    try:
        msg = asyncio.run_coroutine_threadsafe(async_mensagem(mensagem), client.loop)
    except Exception as e:
        print(e)


def desconectado(session, actor):
    try:
        msg = asyncio.run_coroutine_threadsafe(
            async_desconectado(session, actor), client.loop
        )
    except Exception as e:
        print(e)


async def asyncc_mensagem(mensagem):
    canal_texto = client.get_channel(canal)
    print(mensagem)
    try:
        result = await canal_texto.send(mensagem)
    except Exception as e:
        print(e)


async def async_mensagem(mensagem):
    try:
        # obtém o canal de texto pelo ID
        canal_texto = client.get_channel(canal)
        print(mensagem)
        # obtém a mensagem como um objeto BeautifulSoup
        mensagem_html = BeautifulSoup(mensagem, 'html.parser')

        # verifica se há uma tag <img> na mensagem
        img_tag = mensagem_html.find('img')
        converter = html2text.HTML2Text()
        converter.body_width = 0
        if img_tag is None:
            # envia a mensagem sem as tags HTML
            mensagem_sem_tags = converter.handle(str(mensagem_html))
            try:
                result = await canal_texto.send(mensagem_sem_tags)
            except Exception as e:
                print(e)
        else:
            try:
                # obtém a string de base64 da mensagem
                base64_str = unquote(img_tag['src'].split(',')[1])
                print(base64_str)
                # converte a string de base64 em um objeto de imagem
                img_bytes = base64.b64decode(base64_str)
                while len(base64_str) % 4 != 0:
                    base64_str += '='
                img = Image.open(BytesIO(img_bytes))
                # envia a imagem para o canal do Discord
                with BytesIO() as image_binary:
                    img.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    file = discord.File(fp=image_binary, filename='imagem.png')
                # envia a mensagem sem as tags de html junto com a imagem
                img_tag.extract()
                mensagem_sem_tags = converter.handle(str(mensagem_html))
                try:
                    result = await canal_texto.send(mensagem_sem_tags, file=file)
                except Exception as e:
                    print(e)
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)

async def async_movido(session, actor):
    global acao_pendente
    canal_texto = client.get_channel(canal)
    if acao_pendente == 9:
        print(f"mover {autor_mensagem}")
        bot.channels.find_by_name(nome_canal).move_in(autor_mensagem['session'])
        acao_pendente = 8
    elif acao_pendente == 8:
        bot.channels[0].move_in()
        acao_pendente = False

    print(
        f"\U0001F50A {session['name']} conectou "
        f"no canal {bot.channels[session['channel_id']]['name']}"
    )
    try:
        result = await canal_texto.send(
            f"\U0001F50A {session['name']} conectou "
            f"no canal {bot.channels[session['channel_id']]['name']}"
        )
    except Exception as e:
        print(e)


async def async_conectado(user):
    canal_texto = client.get_channel(canal)
    try:
        user.send_text_message(
            f"<p>bem vindo <b>{user['name']}</b> ^_^!</p><br> envie uma mensagem privada para o bot com o comando <b>/ajuda</b> para saber nossos comandos."
        )
    except Exception as e:
        print(e)
    print(
        f"\U0001F50A {user['name']} está conectado "
        f"no canal {bot.channels[user['channel_id']]['name']}"
    )
    try:
        result = await canal_texto.send(
            f"\U0001F50A {user['name']} está conectado "
            f"no canal {bot.channels[user['channel_id']]['name']}"
        )
    except Exception as e:
        print(e)


async def async_desconectado(session, actor):
    print(session, actor)
    canal_texto = client.get_channel(canal)
    print(f"\U0001F507 {session['name']} foi desconectado.")
    try:
        result = await canal_texto.send(
            f"\U0001F507 {session['name']} foi desconectado."
        )
    except Exception as e:
        print(e)


def canal_removido(canal):
    print(canal)
    if canal['name'] in canais_privados.keys():
        try:
            print(f"{canal['name']} removido.")
            canais_privados.pop(canal['name'])
            print(canais_privados)
        except Exception as e:
            print(e)
# Adicionar a função ao callback de recebimento de mensagem de texto
bot.callbacks.add_callback(
    pymumble.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, mensagem_recebida
)
bot.callbacks.add_callback(pymumble.constants.PYMUMBLE_CLBK_USERCREATED, conectado)
bot.callbacks.add_callback(pymumble.constants.PYMUMBLE_CLBK_USERUPDATED, movido)
bot.callbacks.add_callback(pymumble.constants.PYMUMBLE_CLBK_USERREMOVED, desconectado)
bot.callbacks.add_callback(pymumble.constants.PYMUMBLE_CLBK_CHANNELREMOVED, canal_removido)




def processar_horas(horario):
    horario = horario - timedelta(hours=3)
    today = horario.now().date()
    yesterday = today - timedelta(days=1)

    if horario.date() == today:
        return f'Hoje às {horario.strftime("%H:%M")}'
    elif horario.date() == yesterday:
        return f'Ontem às {horario.strftime("%H:%M")}'
    else:
        return horario.strftime("%d/%m/%Y %H:%M")


async def formatar_mensagem(message):
    conteudo = ""
    try:
        if message.reference:
            resposta = message.reference.cached_message
            if resposta:
                conteudo = f"<p>| {markdown.markdown(resposta.content)}</p>"
            else:
                try:
                    resposta = await message.channel.fetch_message(
                        message.reference.message_id
                    )
                except Exception as e:
                    conteudo = f"<p>| {message.reference.message_id}</p>"
                if resposta:
                    conteudo = f"<p>| {markdown.markdown(resposta.content)}</p>"
    except Exception as e:
        print(e)
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type.startswith("image/"):
                image_data = await attachment.read()
                with Image.open(BytesIO(image_data)) as img:
                    img = img.convert("RGB")
                    # Redimensionar a imagem mantendo a proporção original
                    width, height = img.size
                    max_height = 250
                    if height > max_height:
                        ratio = max_height / height
                        width = int(width * ratio)
                        height = max_height
                        img = img.resize((width, height), Image.ANTIALIAS)
                    # Converter a imagem em base64
                    buffered = BytesIO()
                    img.save(buffered, format="JPEG")
                    base64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    conteudo += f'<img src="data:image/jpeg;base64,{base64_data}">'
    conteudo += markdown.markdown(message.content)
    return f"<p><b>{message.author.name}</b> {processar_horas(message.created_at)}</p><p>{conteudo}</p>"
    
# Discord

import discord

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{endereco_ip}:{porta}"))
    bot.channels[0].move_in()
    print(f"(i) Logado como: {client.user.name}")

def encontrar_usuario_por_nome(nome):
    for _, usuario in bot.users.items():
        if usuario['name'] == nome:
            return usuario
    return None

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.channel.id == canal:
        return
    for usuario in usuarios_permitidos:
        usuario_mumble = encontrar_usuario_por_nome(usuario)
        if usuario_mumble:
            usuario_mumble.send_text_message(await formatar_mensagem(message))



client.run(TOKEN)