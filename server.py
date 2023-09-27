import Pyro5.api

@Pyro5.api.expose
class Estoque(object):
    def cadastro_de_usuario(self, name):
        return f'Usuario {name} cadastrado'
    
    


daemon = Pyro5.server.Daemon()         # make a Pyro daemon
ns = Pyro5.api.locate_ns()             # find the name server
uri = daemon.register(Estoque)   # register the greeting maker as a Pyro object
ns.register("estoque", uri)   # register the object with a name in the name server

print("Servidor pronto. Aguardando conexões...")
daemon.requestLoop()                   # start the event loop of the server to wait for calls