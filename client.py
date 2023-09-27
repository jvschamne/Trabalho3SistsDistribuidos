import Pyro5.api

name = input("Qual o nome do Gestor? ").strip()

objeto_estoque = Pyro5.api.Proxy("PYRONAME:estoque")    # use name server object lookup uri shortcut
print(objeto_estoque.hello_gestor(name))