from client import client

token = open("token.txt", "r").read()
client.run(token)

# TODO:
#   Descobrir como fazer stream direto do youtube sem baixar, caso contrário deletar os arquivos DONE
#   Função de playlist
#   Função de stop e skip
#   Função de loop (loopar a mesma música)
#   $gui, retornar aquela imagem
#   Bot deve desconectar após 5 min afk