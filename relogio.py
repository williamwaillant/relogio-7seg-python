# -*- coding: utf-8 -*-
from datetime import datetime
import curses , requests

# Variaveis Globais do programa
size = 1 #tamanho do display
menu = ['Alterar tamanho', 'Alterar Timezone', 'Retornar a hora local' , 'Voltar'] #Lista para criação do menu de configurações
link = "http://worldtimeapi.org/api/timezone/" # Link principal de acesso a API
api_link = "" #Link secundario de acesso a API criado a parti das escolhas do usuario
flag_timezone = 0 #Flag para definir acesso ao timezone local ou escolhido pelo usuario
json_data = [] #Variavel que guarda a lista de timezones consumida pela API
timezone = "" #Varaivel que guarda a escolha de timezone do usario para geraçõa do link secundario

# =============================================================================
# Função para criação e estruturação do segmentos de um digito do display
# Parametros:
#               number ->vetor booleano correspondente aos segmentos do display
#               size -> tamanho do display 
# =============================================================================
def display(number, size=1):
    num_string = [[" "]*(2**size+2) for i in range(2**size+1)]
    if number[0]:
        for i in range(2**size):
            num_string[0][1+i] = ("_")
    if number[1]:
        for i in range(2**(size-1)):
            num_string[1+i][-1] = ("|")
    if number[2]:
        for i in range(2**(size-1)):
            num_string[(2**(size-1))+1+i][-1] = ("|")
    if number[3]:
        for i in range(2**size):
            num_string[-1][1+i] = ("_")
    if number[4]:
        for i in range(2**(size-1)):
            num_string[(2**(size-1))+1+i][0] = ("|")
    if number[5]:
        for i in range(2**(size-1)):
            num_string[1+i][0] = ("|")
    if number[6]:
        for i in range(2**size):
            num_string[2**(size-1)][1+i] = ("_")
    return num_string


# =============================================================================
# Função que  simula  um  multiplexador para definir quais segmentos do display 
# sera ligado dependendo do numero que se deseja criar
# Parametros:
#               number -> valor do numero que se deseja transforma em display
# =============================================================================
def muxDisplay(number):
    if number == 9:
        return (True,True,True,False,False,True,True)
    if number == 8:
        return (True,True,True,True,True,True,True)
    if number == 7:
        return (True,True,True,False,False,False,False)
    if number == 6:
        return (False,False,True,True,True,True,True)
    if number == 5:
        return (True,False,True,True,False,True,True)
    if number == 4:
        return (False,True,True,False,False,True,True)
    if number == 3:
        return (True,True,True,True,False,False,True)
    if number == 2:
        return (True,True,False,True,True,False,True)
    if number == 1:
        return (False,True,True,False,False,False,False)
    if number == 0:
        return (True,True,True,True,True,True,False)

# =============================================================================
# Função  que  concatena  duas matrizes de display cada uma correspondendo a um 
# digito
# Parametros:
#               displayA -> matriz de cacracteres do display
#               displayB -> matriz de cacracteres do display 
# =============================================================================
def concatDisplay(displayA, displayB):
    displayAux = displayA.copy()
    for i in range(len(displayAux)):
        displayAux[i] += displayB[i]
    return displayAux

# =============================================================================
# Função que concatena o simbolo : no final de uma matriz de display
# Parametros: 
#               size -> tamanho do display
# =============================================================================
def divDisplay(size=1):
    string = [[" "]*((2*size)+1) for i in range(2**size+1)]
    string[2**(size-1)][size] = string[(2**(size-1))+1][size] = "o"
    return string

# =============================================================================
# Função para criação de um display de dois digitos, ja tratanto o caso de se
# colocar um 0 a frente de um numero menor que 10
# Parametros:
#               numb -> valor numerico que se deseja criar em formato do
#                       display
#               size -> tamanho do display
# =============================================================================
def numb2Display(numb, size):
    return concatDisplay(display(muxDisplay(numb//10), size), display(muxDisplay(numb%10), size))

# =============================================================================
# função para gerar o display completo no formato hh:mm:ss
# Parametros:
#               h -> valor da hora que se deseja criar em formato do dispaly
#               m -> valor do minuto que se deseja criar em formato do dispaly
#               s -> valor do secundo que se deseja criar em formato do dispaly
#               size -> tamanho do display
# =============================================================================
def hourDisplay(h, m, s, size):
    hour = concatDisplay(numb2Display(h, size), divDisplay(size))
    minutes = concatDisplay(numb2Display(m, size), divDisplay(size))
    seconds = numb2Display(s, size)

    return concatDisplay(concatDisplay(hour, minutes), seconds)

# =============================================================================
# função que printa o menu de configurações na tela do terminal
# Parametros:
#               stdscr -> objeto janela do Curses
# =============================================================================
def print_menu(stdscr, selected_row_idx):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    for idx, row in enumerate(menu):
        x = w//2 - len(row)//2
        y = h//2 - len(menu)//2 + idx
        if idx == selected_row_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, row)
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, x, row)
    stdscr.refresh()
    
# =============================================================================
# Função que consome a API de timezone, cria a janela com a lista de nomes das 
# regiões que a API disponibiliza e recebe a região escolhida pelo usuario
# Parametros:
#               stdscr -> objeto janela do Curses
# =============================================================================
def alter_timezone_region(stdscr):
    curses.echo()
    stdscr.clear()
    curses.curs_set(1)
    stdscr.timeout(0)
    contW = contH = 3
    contH = 3
    text = "Listas de regioes dos fusos:"
    text_resp = "Escolha umas das opcoes e digite o numero dela: "
    text_cancel = "Escolha 0 para voltar"
    global link
    global flag_timezone
    global json_data
    global timezone
    try:
        json_data = requests.get(link).json()
    except:
        print("Erro ao conectar com a API")
        timezone = "API error connecting"
        return
    list_fusos = []
    for i in json_data:
        list_fusos.append(i[0:i.find('/')])
    list_fusos = sorted(set(list_fusos))
    stdscr.addstr(2,3,text)
    for i in range(len(list_fusos)):
        stdscr.addstr(contH,contW,"{" + str(i+1) + "}-> " + list_fusos[i])
        if (i+1)%5 == 0:
            contH += 1
            contW = 3
        else:
            contW += 18
    stdscr.addstr(contH+1, 3, text_resp)
    stdscr.addstr(contH+2, 3, text_cancel)
    try:
        aux = int(stdscr.getstr(contH+1, 3+len(text_resp)+1, 3))
    except:
        alter_timezone_region(stdscr)
        return
    if aux == 0:
        return
    if aux > 0 and aux < (len(list_fusos)+1):
        alter_timezone_city(stdscr,list_fusos[aux-1]) 
    else:
        alter_timezone_region(stdscr)
        return
    stdscr.refresh()

# =============================================================================
# Função  que  a  partir  da  escolha  da  região cria a janela com a lista das 
# cidades  que a API disponibiliza e recebe a resposta final de qual timezone o 
# usuario deseja
# Parametros:
#               stdscr -> objeto janela do Curses
#               region -> id da timezone          
# =============================================================================
def alter_timezone_city(stdscr,region):
    global api_link
    global link
    global json_data
    global flag_timezone
    curses.echo()
    stdscr.clear()
    curses.curs_set(1)
    stdscr.timeout(0)
    text = "Listas de regioes dos fusos:"
    text_resp = "Escolha umas das opcoes e digite o numero dela: "
    text_cancel = "Escolha 0 para voltar"
    contW = contH = 3
    list_fusos = []
    for i in json_data:
        if i.find(region) >= 0 :
            list_fusos.append(i)
    stdscr.addstr(2,3,text)
    for i in range(len(list_fusos)):
        stdscr.addstr(contH,contW,"{" + str(i+1) + "}-> " + list_fusos[i])
        if (i+1)%5 == 0:
            contH += 1
            contW = 3
        else:
            contW += 37
    stdscr.addstr(contH+1, 3, text_resp)
    stdscr.addstr(contH+2, 3, text_cancel)
    try:
        aux = int(stdscr.getstr(contH+1, 3+len(text_resp)+1, 3))
    except:
        alter_timezone_city(stdscr,region)
        return
    if aux == 0:
        return
    if aux > 0 and aux < (len(list_fusos)+1):
        flag_timezone = 1
        api_link = link + list_fusos[aux-1]   
    else:
        alter_timezone_city(stdscr,region)
        return
    stdscr.refresh()
    
# =============================================================================
# Função que cria a janela de alterar o tamanho do display a partir de uma
# entrada do usuario 
# Parametros:
#               stdscr -> objeto janela do Curses          
# =============================================================================
def alter_size(stdscr):
    curses.echo()
    global size
    text = "Escolha o novo tamanho(1 a 5): "
    stdscr.clear()
    curses.curs_set(1)
    stdscr.timeout(0)
    h, w = stdscr.getmaxyx()
    x = w//2 - len(text)//2
    y = h//2
    stdscr.addstr(y, x, text)
    stdscr.refresh()
    try:
        size = int(stdscr.getstr(y, x+len(text)+1, 1))
    except:
        alter_size(stdscr)
        return
    if size > 5:
        size = 5
    if size < 1:
        size = 1
    stdscr.refresh()

# =============================================================================
# Função para ajustar a hora de acordo com o timezone escolhido 
# Parametros:
#               fusoH -> valor das horas que deseja somar
#               hour -> valor das hora atual
# =============================================================================
def convert_fusoH(fusoH, hour):
    result = 3 + fusoH
    result += hour
    if result > 23:
        return result - 24
    if result < 0:
        return 24 + result
    else:
        return result

# =============================================================================
# Função para ajustar os minutos de acordo com o timezone escolhido
# Parametros:
#               fusoM -> valor dos minutos que deseja somar
#               minute -> valor dos minuto da hora atual
# =============================================================================
def convert_fusoM(fusoM, minute):
    result = 0 + fusoM
    result += minute
    return result

# =============================================================================
# Função que cria a janela do menu de configurações
# Parametros:
#               stdscr -> objeto janela do Curses          
# =============================================================================
def start_menu(stdscr):
    global flag_timezone
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    current_row = 0

    print_menu(stdscr, current_row)
    while 1:
        key_menu = stdscr.getch()

        if key_menu == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key_menu == curses.KEY_DOWN and current_row < len(menu)-1:
            current_row += 1
        elif key_menu == curses.KEY_ENTER or key_menu in [10, 13]:
            if current_row == 0:
                alter_size(stdscr)
                stdscr.clear()
                curses.curs_set(0)
                stdscr.timeout(100)
                curses.noecho()
                break
            if current_row == 1:
                alter_timezone_region(stdscr)
                stdscr.clear()
                curses.curs_set(0)
                stdscr.timeout(100)
                curses.noecho()
                break
            if current_row == 2:
                flag_timezone = 0
                stdscr.clear()
                break
            if current_row == len(menu)-1:
                stdscr.clear()
                break
        print_menu(stdscr, current_row)

# =============================================================================
# Função   principal  que  gera  o  Display  complete  de  acordo  com  a  hora 
# pré-estabelecida  e  cria  a  janela primaria do programa rodando o display e
# atualizando em tempo real
# Parametros:
#               stdscr -> objeto janela do Curses
# =============================================================================
def playDisplay(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)
    global size
    global flag_timezone
    global api_link
    global timezone 
    aux = ""
    fusoH = fusoM = 0
    h , w = stdscr.getmaxyx()
    if h < 40 or w < 230:
        print("Por favor deixe seu terminal em tela cheia antes de executar o programa!")
        exit()
    while 1:
        stdscr.refresh()
        if flag_timezone == 0:   
            now = datetime.now()
            numb = hourDisplay(now.hour, now.minute, now.second, size)
            timezone = "America/Brasil/Brasilia"
            for i in range(len(numb)):
                stdscr.addstr(i, 0, ''.join([str(elem) for elem in numb[i]]))
        else:
            if flag_timezone == 1:
                try:
                    json_data = requests.get(api_link).json()
                    flag_timezone = 2
                    aux = json_data['utc_offset']
                    timezone = json_data['timezone']
                    stdscr.clear()
                except:
                    print("Erro ao conectar com a API")
                    continue
            now = datetime.now()
            fusoH = int(aux[0:3])
            fusoM = int(aux[4:6])
            fusoH = convert_fusoH(fusoH, now.hour)
            fusoM = convert_fusoM(fusoM, now.minute)
            if fusoM > 59:
                fusoM -= 60
                fusoH += 1
            numb = hourDisplay(fusoH, fusoM, now.second, size)
            for i in range(len(numb)):
                stdscr.addstr(i, 0, ''.join([str(elem) for elem in numb[i]]))
                
        key = stdscr.getch()
        opt = curses.KEY_UP
        if key in [27,curses.KEY_LEFT,curses.KEY_RIGHT,curses.KEY_F1]:
            opt = key      
            
        if opt == curses.KEY_RIGHT:
            size += 1
            stdscr.clear()    
        if opt == curses.KEY_LEFT:
            size -= 1
            stdscr.clear()
        if opt == 27:
            break
        if opt == curses.KEY_F1:
            start_menu(stdscr)
        
        if size == 0:
            size = 1
        if size == 6:
            size = 5
            
        text_size = "Aperte <- e -> para alterar o tamanho do relogio! | tamanho atual: " + str(size) + " | Timezone atual: " + timezone
        stdscr.addstr((2**size+2),0,text_size)
        text_settings = "Aperte F1 para entrar nas configuracoes"
        stdscr.addstr((2**size+3),0,text_settings)
        text_exit = "Aperte ESC para sair do programa"
        stdscr.addstr((2**size+4),0,text_exit)


# =============================================================================
# inicialização do programa. a função curses.wrapper inicializa a janela stdscr
# e passa como parametro para um função principal
# =============================================================================
curses.wrapper(playDisplay)
