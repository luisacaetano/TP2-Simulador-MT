#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulador de Máquina de Turing
Autor: Luisa Caetano Araújo
Trabalho Prático - Fundamentos Teóricos da Computação
"""

import sys
import re


class Tape:
    """Representa a fita infinita da Máquina de Turing."""

    def __init__(self, initial_word=""):
        """Inicializa a fita com uma palavra inicial."""
        self.cells = {}  # Dicionário para armazenar as células da fita
        self.head = 0    # Posição do cabeçote
        for i, char in enumerate(initial_word):
            if char != ' ':  # Espaço é tratado como branco
                self.cells[i] = char

    def read(self):
        """Lê o símbolo na posição atual do cabeçote."""
        return self.cells.get(self.head, '_')

    def write(self, symbol):
        """Escreve um símbolo na posição atual do cabeçote."""
        if symbol == '_':
            if self.head in self.cells:
                del self.cells[self.head]
        else:
            self.cells[self.head] = symbol

    def move(self, direction):
        """Move o cabeçote: 'e' (esquerda), 'd' (direita), 'i' (imóvel)."""
        if direction == 'e':
            self.head -= 1
        elif direction == 'd':
            self.head += 1
        # 'i' = imóvel, não faz nada

    def get_display(self, left_chars=20, right_chars=20, left_delim='(', right_delim=')'):
        """Retorna a representação visual da fita com o cabeçote."""
        left_part = ""
        for i in range(self.head - left_chars, self.head):
            left_part += self.cells.get(i, '_')

        current = self.cells.get(self.head, '_')

        right_part = ""
        for i in range(self.head + 1, self.head + 1 + right_chars):
            right_part += self.cells.get(i, '_')

        return f"{left_part}{left_delim}{current}{right_delim}{right_part}"

    def get_content(self):
        """Retorna o conteúdo não-branco da fita."""
        if not self.cells:
            return ""
        min_pos = min(self.cells.keys())
        max_pos = max(self.cells.keys())
        result = ""
        for i in range(min_pos, max_pos + 1):
            result += self.cells.get(i, '_')
        return result.strip('_')


class Transition:
    """Representa uma transição da Máquina de Turing."""

    def __init__(self, current_state, current_symbol, new_symbol, movement, new_state, has_breakpoint=False):
        """Inicializa uma transição com seus parâmetros."""
        self.current_state = current_state    # Estado atual
        self.current_symbol = current_symbol  # Símbolo lido
        self.new_symbol = new_symbol          # Símbolo a escrever
        self.movement = movement              # Movimento do cabeçote
        self.new_state = new_state            # Novo estado
        self.has_breakpoint = has_breakpoint  # Indica se há breakpoint


class BlockCall:
    """Representa uma chamada de bloco."""

    def __init__(self, current_state, block_name, return_state):
        """Inicializa uma chamada de bloco."""
        self.current_state = current_state  # Estado que dispara a chamada
        self.block_name = block_name        # Nome do bloco a chamar
        self.return_state = return_state    # Estado de retorno


class Block:
    """Representa um bloco de código da Máquina de Turing."""

    def __init__(self, name, initial_state):
        """Inicializa um bloco com nome e estado inicial."""
        self.name = name
        self.initial_state = initial_state
        self.transitions = []   # Lista de transições do bloco
        self.block_calls = []   # Lista de chamadas de bloco


class TuringMachine:
    """Simulador da Máquina de Turing."""

    def __init__(self):
        """Inicializa o simulador."""
        self.blocks = {}              # Dicionário de blocos
        self.tape = None              # Fita da máquina
        self.current_block = "main"   # Bloco em execução
        self.current_state = 1        # Estado atual
        self.call_stack = []          # Pilha de chamadas de bloco
        self.halted = False           # Indica se a máquina parou
        self.error = None             # Mensagem de erro
        self.memorized_char = {}      # Caractere memorizado por bloco (para @)
        self.left_delim = '('         # Delimitador esquerdo do cabeçote
        self.right_delim = ')'        # Delimitador direito do cabeçote

    def parse_program(self, filename):
        """Faz o parsing do arquivo de programa e carrega os blocos."""
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_block = None

        for line_num, line in enumerate(lines, 1):
            # Remove comentários (tudo após ';')
            if ';' in line:
                comment_pos = line.index(';')
                line = line[:comment_pos]

            line = line.strip()
            if not line:
                continue

            # Verifica se há breakpoint no final da linha
            has_breakpoint = line.endswith('!')
            if has_breakpoint:
                line = line[:-1].strip()

            tokens = line.split()
            if not tokens:
                continue

            # Comando: bloco <identificador> <estado inicial>
            if tokens[0] == 'bloco':
                if len(tokens) >= 3:
                    block_name = tokens[1]
                    initial_state = int(tokens[2])
                    current_block = Block(block_name, initial_state)
                    self.blocks[block_name] = current_block
                continue

            # Comando: fim (encerra o bloco atual)
            if tokens[0] == 'fim':
                current_block = None
                continue

            if current_block is None:
                continue

            # Chamada de bloco: <estado atual> <identificador de bloco> <estado de retorno>
            if len(tokens) == 3:
                try:
                    current_state = int(tokens[0])
                    block_name = tokens[1]
                    return_state = tokens[2]
                    if return_state == 'pare':
                        return_state = 'pare'
                    else:
                        return_state = int(return_state)
                    current_block.block_calls.append(BlockCall(current_state, block_name, return_state))
                except ValueError:
                    pass

            # Transição: <estado atual> <símbolo atual> -- <novo símbolo> <movimento> <novo estado>
            elif len(tokens) >= 5 and tokens[2] == '--':
                current_state = tokens[0]
                if current_state != '*':
                    current_state = int(current_state)

                current_symbol = tokens[1]
                new_symbol = tokens[3]
                movement = tokens[4]
                new_state = tokens[5] if len(tokens) > 5 else 'pare'

                if new_state not in ('retorne', 'pare', '*'):
                    try:
                        new_state = int(new_state)
                    except ValueError:
                        pass

                trans = Transition(current_state, current_symbol, new_symbol, movement, new_state, has_breakpoint)
                current_block.transitions.append(trans)

    def format_config(self):
        """Formata a configuração instantânea para exibição."""
        block_name = self.current_block[:16].rjust(16, '.')
        state_str = str(self.current_state).zfill(4)
        tape_display = self.tape.get_display(20, 20, self.left_delim, self.right_delim)
        return f"{block_name}.{state_str}: {tape_display}"

    def find_transition(self):
        """Encontra a transição aplicável ao estado e símbolo atuais."""
        block = self.blocks.get(self.current_block)
        if not block:
            return None, None

        current_symbol = self.tape.read()

        # Primeiro verifica chamadas de bloco
        for call in block.block_calls:
            if call.current_state == self.current_state or call.current_state == '*':
                return None, call

        # Depois verifica transições (busca a de maior prioridade)
        best_trans = None
        best_priority = -1

        for trans in block.transitions:
            state_match = (trans.current_state == self.current_state or trans.current_state == '*')

            if not state_match:
                continue

            symbol_match = False
            priority = 0

            # Prioridade maior para match exato de estado
            if trans.current_state == self.current_state:
                priority += 10

            # Prioridade por tipo de símbolo: exato > @ > *
            if trans.current_symbol == current_symbol:
                symbol_match = True
                priority += 3
            elif trans.current_symbol == '@':
                symbol_match = True
                priority += 2
            elif trans.current_symbol == '*':
                symbol_match = True
                priority += 1

            if symbol_match and priority > best_priority:
                best_trans = trans
                best_priority = priority

        return best_trans, None

    def step(self):
        """Executa um passo da máquina. Retorna (sucesso, breakpoint)."""
        if self.halted:
            return False, False

        trans, call = self.find_transition()

        # Executa chamada de bloco
        if call:
            self.call_stack.append((self.current_block, call.return_state))
            self.current_block = call.block_name
            block = self.blocks.get(self.current_block)
            if block:
                self.current_state = block.initial_state
            else:
                self.error = f"Bloco '{call.block_name}' não encontrado"
                self.halted = True
                return False, False
            return True, False

        # Executa transição
        if trans:
            # Memoriza caractere se a transição usa @ no símbolo atual
            if trans.current_symbol == '@':
                self.memorized_char[self.current_block] = self.tape.read()

            # Determina o símbolo a ser escrito
            new_symbol = trans.new_symbol
            if new_symbol == '*':
                new_symbol = self.tape.read()  # Mantém o símbolo atual
            elif new_symbol == '@':
                if self.current_block in self.memorized_char:
                    new_symbol = self.memorized_char[self.current_block]
                else:
                    self.error = "Uso de '@' sem caractere memorizado"
                    self.halted = True
                    return False, False

            # Escreve na fita e move o cabeçote
            self.tape.write(new_symbol)
            self.tape.move(trans.movement)

            # Determina o próximo estado
            new_state = trans.new_state
            if new_state == 'pare':
                self.halted = True
                return True, trans.has_breakpoint
            elif new_state == 'retorne':
                # Retorna do bloco atual para o bloco chamador
                if self.call_stack:
                    self.current_block, return_state = self.call_stack.pop()
                    if return_state == 'pare':
                        self.halted = True
                    else:
                        self.current_state = return_state
                else:
                    self.halted = True
                return True, trans.has_breakpoint
            elif new_state != '*':
                self.current_state = new_state

            return True, trans.has_breakpoint

        # Nenhuma transição encontrada - erro
        self.error = f"Sem transição para estado {self.current_state} com símbolo '{self.tape.read()}'"
        self.halted = True
        return False, False

    def run(self, mode='resume', step_count=10):
        """Executa o programa no modo especificado (resume, verbose ou step)."""
        if 'main' not in self.blocks:
            print("Erro: bloco 'main' não encontrado")
            return

        # Inicializa a execução no bloco main
        self.current_block = 'main'
        self.current_state = self.blocks['main'].initial_state

        lines_shown = 0
        last_option = mode

        # Loop principal de execução
        while not self.halted:
            # Exibe configuração nos modos verbose e step
            if mode == 'verbose' or mode == 'step':
                print(self.format_config())
                lines_shown += 1

            success, breakpoint = self.step()

            if not success and not self.halted:
                break

            # No modo step, pausa após exibir n linhas
            if mode == 'step' and lines_shown >= step_count:
                option = input("\nForneca opcao (r, v, s): ").strip().lower()
                if not option:
                    option = last_option[0] if last_option else 's'

                if option == 'r':
                    mode = 'resume'
                elif option == 'v':
                    mode = 'verbose'
                elif option.startswith('s'):
                    mode = 'step'
                    parts = option.split()
                    if len(parts) > 1:
                        try:
                            step_count = int(parts[1])
                        except:
                            pass

                last_option = mode
                lines_shown = 0

            # Pausa em breakpoints
            if breakpoint:
                print(self.format_config())
                option = input("\nBreakpoint! Forneca opcao (r, v, s): ").strip().lower()
                if option == 'r':
                    mode = 'resume'
                elif option == 'v':
                    mode = 'verbose'
                elif option.startswith('s'):
                    mode = 'step'
                    lines_shown = 0

        # Exibe erro se houver
        if self.error:
            print(f"\nErro: {self.error}")

        # Exibe resultado final
        print(f"\nResultado final: {self.tape.get_content()}")


def print_banner(author="Luisa Caetano Araujo"):
    """Exibe o banner do simulador."""
    print()
    print("Simulador de Maquina de Turing")
    print(f"Autor: {author}")
    print()


def main():
    """Função principal do simulador."""
    args = sys.argv[1:]

    # Exibe ajuda se não houver argumentos
    if not args:
        print("Uso: simturing <opcoes> <programa>")
        print("Opcoes:")
        print("  -r, -resume    Executa ate o fim e imprime resultado")
        print("  -v, -verbose   Mostra execucao passo a passo")
        print("  -s, -step <n>  Mostra n passos e aguarda opcao")
        print("  -head <delim>  Define delimitadores do cabecote (ex: <>)")
        sys.exit(1)

    # Valores padrão
    mode = 'resume'
    step_count = 10
    head_delim = '()'
    program_file = None

    # Processa argumentos da linha de comando
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ('-r', '-resume'):
            mode = 'resume'
        elif arg in ('-v', '-verbose'):
            mode = 'verbose'
        elif arg in ('-s', '-step'):
            mode = 'step'
            if i + 1 < len(args) and args[i + 1].isdigit():
                i += 1
                step_count = int(args[i])
        elif arg == '-head':
            if i + 1 < len(args):
                i += 1
                head_delim = args[i]
        else:
            program_file = arg
        i += 1

    # Verifica se o arquivo foi especificado
    if not program_file:
        print("Erro: arquivo de programa nao especificado")
        sys.exit(1)

    print_banner()

    # Cria e configura a máquina de Turing
    tm = TuringMachine()

    # Define delimitadores do cabeçote
    if len(head_delim) >= 2:
        tm.left_delim = head_delim[0]
        tm.right_delim = head_delim[1]

    # Carrega o programa
    try:
        tm.parse_program(program_file)
    except FileNotFoundError:
        print(f"Erro: arquivo '{program_file}' nao encontrado")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao ler programa: {e}")
        sys.exit(1)

    # Solicita a palavra inicial
    initial_word = input("Forneca a palavra inicial: ")
    print()

    # Inicializa a fita e executa o programa
    tm.tape = Tape(initial_word)
    tm.run(mode, step_count)


if __name__ == '__main__':
    main()
