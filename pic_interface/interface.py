import serial
import json
import re


serial_port = None
first = 0
port = None
baud = 0
desth_timeout = 0


#status, config

def print_serial():
    global serial_port

    while True:
        pic_message = serial_port.read_until(b'\r')
        pic_message = pic_message.decode(encoding='ascii')
        if len(pic_message.strip()) > 1: #Apanha os casos em que o pic manda /n/r
            print(pic_message.strip())

def receive_data_from_exp():
    global serial_port
    global first 
    if first == 0:
        first =1
        print("ENCONTREI INFO\nEXPERIENCIA COMECOU")
        return "DATA_START"
    elif first == 2:
        print("ENCONTREI INFO\nEXPERIENCIA ACABOU")
        return "DATA_END"
    else:
        pic_message = serial_port.read_until(b'\r')
        pic_message = pic_message.decode(encoding='ascii')
        print("MENSAGEM DO Arduino:\n")
        print(pic_message)
        print("\-------- --------/\n")
        #1       3.1911812       9.7769165       21.2292843      25.72
        # print("ENCONTREI INFO\nDADOS NA PORTA")
        # pic_message = pic_message.strip()
        # pic_message = pic_message.split("\t")
        # pic_message = '{"Sample_number":"'+str(pic_message[0])+\
        #     '","Val1":"'+str(pic_message[1])+'","Val2":"'+str(pic_message[2])+\
        #     '","Val3":"'+str(pic_message[3])+'","Val4":"'+str(pic_message[4])+'"}'
        return pic_message
    
#ALGURES AQUI HA BUG QUANDO NAO ESTA EM NENHUMA DAS PORTAS
def try_to_lock_experiment(config_json, serial_port):
    #LOG_INFO
    print("AH PROCURA DO PIC NA PORTA SERIE")
    pic_message = serial_port.read_until(b'\r')
    pic_message = pic_message.decode(encoding='ascii')
    pic_message = pic_message.strip()
    print("MENSAGEM DO PIC:\n")
    print(pic_message)
    print("\-------- --------/\n")
    return True
    # down there is a error for the arduino k

    # Posso fazer no futuro uma mensagem de detecção da experiencia do tipo
    # mandar a mensagem "Get Id" e o Arduino parar de mandar msg e mandar 5 msg de com o nome dele
    # assim assegurando a experiencia correta.

    # match = re.search(r"^(IDS)\s(?P<exp_name>[^ \t]+)\s(?P<exp_state>[^ \t]+)$",pic_message)
    # if match.group("exp_name") == config_json['id']:
    #     #LOG_INFO
    #     print("ENCONTREI O PIC QUE QUERIA NA PORTA SERIE")
    #     if match.group("exp_state") == "STOPED":
    #         return True
    #     else:
    #         if do_stop():
    #             return True
    #         else:
    #             return False
    # else:
    #     #LOG INFO
    #     print("NAO ENCONTREI O PIC QUE QUERIA NA PORTA SERIE")
    #     return False

#DO_INIT - Abre a ligacao com a porta serie
#NOTAS: possivelmente os returns devem ser jsons com mensagens de erro
#melhores, por exemplo, as portas não existem ou não está o pic em nenhuma
#delas outra hipotese é retornar ao cliente exito ou falha
#e escrever detalhes no log do sistema
def do_init(config_json):
    global serial_port
    global port
    global baud
    global desth_timeout

    if 'serial_port' in config_json:
        for exp_port in config_json['serial_port']['ports_restrict']:
            print("A tentar abrir a porta "+exp_port+"\n")
            try:
                #alterar esta função para aceitar mais definições do json
                #é preciso uma função para mapear os valores para as constantes da porta série
                #e.g. - 8 bits de data -> serial.EIGHTBITS; 1 stopbit -> serial.STOPBITS_ONE
                port = exp_port
                baud = int(config_json['serial_port']['baud'])
                desth_timeout = int(config_json['serial_port']['death_timeout'])
                serial_port = serial.Serial(port = exp_port,\
                                                    baudrate=int(config_json['serial_port']['baud']),\
                                                    timeout = int(config_json['serial_port']['death_timeout']))
            except serial.SerialException:
                #LOG_WARNING: couldn't open serial port exp_port. Port doesnt exist or is in use
                pass
            else:
                if try_to_lock_experiment(config_json, serial_port) :
                    break
                else:
                    serial_port.close()
        
        if serial_port.is_open :
            #LOG_INFO : EXPERIMENT FOUND. INITIALIZING EXPERIMENT
            print("Consegui abrir a porta e encontrar a experiencia\n")
            #Mudar para números. Return 0 e mandar status
            return True
        else:
            #SUBSTITUIR POR LOG_ERROR : couldn't find the experiment in any of the configured serial ports
            print("Nao consegui abrir a porta e encontrar a experiencia\n")
            #return -1
            return False
    else:
        #LOG_ERROR - Serial port not configured on json.
        #return -2
        return False

def do_config(config_json) :
    global serial_port
    Arduino_message =  "Do not need config"
    do_stop()
    return Arduino_message, True

def do_start() :
    global serial_port
    global first
    global port
    global baud
    global desth_timeout
    first = 0
    if serial_port.is_open :
        pass
    else:
        serial_port = serial.Serial(port = port,\
                                    baudrate=baud,\
                                    timeout = desth_timeout)
        # serial_port.reset_input_buffer()
    return True
        #elif "STOPED" or "CONFIGURED" or "RESETED" in pic_message.decode(encoding='ascii') :
        #    return False
        #Aqui não pode ter else: false senão rebenta por tudo e por nada
        #tem de se apontar aos casos especificos -_-
    

def do_stop() :
    global serial_port
    global first

    first = 2 

    if serial_port.is_open :
        # serial_port.reset_input_buffer()
        serial_port.close()
    
    return True
        #Aqui não pode ter else: false senão rebenta por tudo e por nada
        #tem de se apontar aos casos especificos -_-
        
    

def do_reset() :
    global serial_port

    do_stop()
    do_start()

    return True
    
        #Aqui não pode ter else: false senão rebenta por tudo e por nada
        #tem de se apontar aos casos especificos -_-

#get_status placeholder
def get_status():
    global serial_port

    print("Esta funcao ainda nao faz nada\n")
    return True



if __name__ == "__main__":
    import sys
    import threading
    
    fp = open("./exp_config.json","r")
    config_json = json.load(fp)
    #config_json = json.loads('{}')
    if not do_init(config_json):
        sys.exit("Não deu para abrir a porta. F")
    printer_thread = threading.Thread(target=print_serial)
    printer_thread.start()
    while True:
        cmd = input()+"\r"
        cmd = cmd.encode(encoding='ascii')
        serial_port.write(cmd)