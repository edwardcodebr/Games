import pygame
import sys
import math
import os # Módulo para lidar com caminhos de arquivos

# --- Inicialização ---
pygame.init()
pygame.font.init()
pygame.mixer.init() # Inicializa o mixer de áudio

# --- Constantes do Jogo ---
LARGURA_TELA = 800
ALTURA_TELA = 600
TELA = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("TBH Criatura: O Jogo")

# --- Cores ---
AZUL_CRIATURA = (65, 105, 225)
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERDE_GRAMA = (34, 139, 34)
MARROM_TERRA = (139, 69, 19)
AZUL_CEU_DIA = (135, 206, 250)
AZUL_CEU_NOITE = (25, 25, 112)
VERMELHO_COKE = (220, 20, 60)
VERMELHO_VIDA = (255, 0, 0)
CINZA_ESCURO = (50, 50, 50)
CINZA_CLARO = (100, 100, 100)
ROSA_BOYKISSER = (255, 182, 193)
VERDE_DRAGAO = (0, 100, 0)
AMARELO_CHIPS = (255, 215, 0)
AMARELO_JOINHA = (255, 223, 0)
CORES_ARCOIRIS = [(255,0,0), (255,127,0), (255,255,0), (0,255,0), (0,0,255), (75,0,130), (148,0,211)]

# --- Configurações Gerais ---
FPS = 60
RELÓGIO = pygame.time.Clock()
VELOCIDADE_JOGADOR = 5
FORCA_PULO = 16
GRAVIDADE = 0.8

# --- Fontes ---
FONTE_PADRAO = pygame.font.SysFont('Consolas', 24)
FONTE_MENU = pygame.font.SysFont('Consolas', 32, bold=True)
FONTE_TITULO = pygame.font.SysFont('Arial', 72, bold=True)
FONTE_CREDITOS = pygame.font.SysFont('Arial', 20)

# --- ÁUDIO (VERSÃO MELHORADA E À PROVA DE ERROS) ---

# Encontra o caminho absoluto para a pasta onde o script está
# Isso garante que ele sempre encontre a pasta 'sons', não importa de onde o jogo seja executado
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

try:
    # Usa o BASE_DIR para construir o caminho completo para cada arquivo
    MUSICA_MENU = os.path.join(BASE_DIR, 'sons', 'menusong.mp3')
    MUSICA_FASE = os.path.join(BASE_DIR, 'sons', 'stagesong.mp3')
    MUSICA_CHEFE = os.path.join(BASE_DIR, 'sons', 'bossfightsong.mp3')
except pygame.error as e:
    print(f"Aviso: Não foi possível carregar um ou mais arquivos de música: {e}")
    MUSICA_MENU, MUSICA_FASE, MUSICA_CHEFE = None, None, None

musica_atual = None

# --- FUNÇÃO GERENCIADORA DE MÚSICA ---
def tocar_musica(nova_musica):
    global musica_atual
    if not nova_musica or musica_atual == nova_musica:
        return 
    
    pygame.mixer.music.fadeout(500)
    pygame.mixer.music.load(nova_musica)
    pygame.mixer.music.play(loops=-1, start=0.0, fade_ms=500)
    musica_atual = nova_musica
    pygame.mixer.music.set_volume(0.5)


# --- Grupos de Sprites ---
plataformas_grupo = pygame.sprite.Group()
inimigos_grupo = pygame.sprite.Group()
projeteis_grupo = pygame.sprite.Group()
todos_os_sprites = pygame.sprite.Group()

# --- Classes de Jogo ---
class BalaoDeFala:
    def __init__(self, texto, duracao_segundos):
        self.texto_surf = FONTE_PADRAO.render(texto, True, PRETO)
        padding = 10
        largura_balao = self.texto_surf.get_width() + padding * 2
        altura_balao = self.texto_surf.get_height() + padding * 2
        self.rect = pygame.Rect(0, 0, largura_balao, altura_balao)
        self.duracao = duracao_segundos * FPS
    def update(self, jogador_rect):
        self.duracao -= 1
        if self.duracao <= 0: return False
        self.rect.centerx = jogador_rect.centerx
        self.rect.bottom = jogador_rect.top - 10
        self.rect.clamp_ip(TELA.get_rect())
        return True
    def desenhar(self, tela):
        pygame.draw.rect(tela, BRANCO, self.rect, border_radius=10)
        pontos = [(self.rect.centerx - 8, self.rect.bottom), (self.rect.centerx + 8, self.rect.bottom), (self.rect.centerx, self.rect.bottom + 8)]
        pygame.draw.polygon(tela, BRANCO, pontos)
        tela.blit(self.texto_surf, (self.rect.x + 10, self.rect.y + 10))

class Jogador(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.largura, self.altura = 40, 50
        self.rect = pygame.Rect(x, y, self.largura, self.altura - 10)
        self.vel_y, self.pulando, self.imune_timer = 0, False, 0
    def mover(self):
        dx, dy = 0, 0
        if self.imune_timer > 0: self.imune_timer -= 1
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT]: dx = -VELOCIDADE_JOGADOR
        if teclas[pygame.K_RIGHT]: dx = VELOCIDADE_JOGADOR
        if teclas[pygame.K_SPACE] and not self.pulando:
            self.vel_y = -FORCA_PULO
            self.pulando = True
            # som_pulo.play() foi removido daqui
        self.vel_y += GRAVIDADE
        if self.vel_y > 10: self.vel_y = 10
        dy += self.vel_y
        for p in plataformas_grupo:
            if p.rect.colliderect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height): dx = 0
            if p.rect.colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                if self.vel_y >= 0:
                    dy = p.rect.top - self.rect.bottom
                    self.vel_y, self.pulando = 0, False
                elif self.vel_y < 0:
                    dy = p.rect.bottom - self.rect.top
                    self.vel_y = 0
        if self.rect.left + dx < 0: dx = -self.rect.left
        if self.rect.right + dx > LARGURA_TELA: dx = LARGURA_TELA - self.rect.right
        if self.rect.top > ALTURA_TELA: return "GAME_OVER"
        self.rect.x += dx
        self.rect.y += dy
        return None
    def desenhar(self, tela):
        if self.imune_timer > 0 and self.imune_timer % 10 < 5: return
        pygame.draw.rect(tela, AZUL_CRIATURA, (self.rect.x, self.rect.y + 10, self.largura, self.altura - 15), border_radius=8)
        pygame.draw.rect(tela, AZUL_CRIATURA, (self.rect.x + 5, self.rect.bottom - 5, 8, 10))
        pygame.draw.rect(tela, AZUL_CRIATURA, (self.rect.right - 13, self.rect.bottom - 5, 8, 10))
        pygame.draw.circle(tela, BRANCO, (self.rect.centerx - 8, self.rect.y + 20), 5)
        pygame.draw.circle(tela, BRANCO, (self.rect.centerx + 8, self.rect.y + 20), 5)
        pygame.draw.circle(tela, PRETO, (self.rect.centerx - 8, self.rect.y + 20), 2)
        pygame.draw.circle(tela, PRETO, (self.rect.centerx + 8, self.rect.y + 20), 2)

class Inimigo(pygame.sprite.Sprite):
    def __init__(self, x, y): super().__init__(); self.rect = pygame.Rect(x, y, 50, 50); self.direcao, self.contador_movimento = 1, 0
    def update(self):
        self.rect.x += self.direcao; self.contador_movimento += 1
        if self.contador_movimento > 50: self.direcao *= -1; self.contador_movimento = 0
    def desenhar(self, tela):
        pygame.draw.rect(tela, BRANCO, self.rect, border_radius=15)
        pygame.draw.polygon(tela, BRANCO, [(self.rect.left, self.rect.top + 15), (self.rect.left + 15, self.rect.top), (self.rect.left + 30, self.rect.top + 15)])
        pygame.draw.polygon(tela, BRANCO, [(self.rect.right, self.rect.top + 15), (self.rect.right - 15, self.rect.top), (self.rect.right - 30, self.rect.top + 15)])
        pygame.draw.line(tela, PRETO, (self.rect.centerx - 10, self.rect.centery), (self.rect.centerx - 5, self.rect.centery + 5), 2)
        pygame.draw.line(tela, PRETO, (self.rect.centerx + 10, self.rect.centery), (self.rect.centerx + 5, self.rect.centery + 5), 2)
        pygame.draw.line(tela, PRETO, (self.rect.centerx, self.rect.centery + 5), (self.rect.centerx, self.rect.centery + 10), 2)
        pygame.draw.line(tela, PRETO, (self.rect.centerx - 3, self.rect.centery + 10), (self.rect.centerx + 3, self.rect.centery + 10), 2)
        pygame.draw.circle(tela, ROSA_BOYKISSER, (self.rect.left + 15, self.rect.centery + 10), 5)
        pygame.draw.circle(tela, ROSA_BOYKISSER, (self.rect.right - 15, self.rect.centery + 10), 5)

class DragaoBoss(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, 120, 100)
        self.hp_max, self.hp = 10, 10
        self.vel_y, self.vel_x = 3, 3
        self.limite_superior, self.limite_inferior = 20, ALTURA_TELA - 40
        self.limite_esquerdo, self.limite_direito = 20, LARGURA_TELA - self.rect.width - 20
        self.ultimo_tiro, self.cooldown_tiro = pygame.time.get_ticks(), 1300
    def update(self):
        self.rect.y += self.vel_y; self.rect.x += self.vel_x
        if self.rect.top <= self.limite_superior: self.vel_y = abs(self.vel_y)
        elif self.rect.bottom >= self.limite_inferior: self.vel_y = -abs(self.vel_y)
        if self.rect.left <= self.limite_esquerdo: self.vel_x = abs(self.vel_x)
        elif self.rect.right >= self.limite_direito: self.vel_x = -abs(self.vel_x)
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro > self.cooldown_tiro:
            self.ultimo_tiro = agora
            projetil = Projetil(self.rect.left - 20, self.rect.centery - 10)
            projeteis_grupo.add(projetil); todos_os_sprites.add(projetil)
    def tomar_dano(self):
        self.hp -= 1
        if self.hp <= 0: self.kill(); return True
        return False
    def desenhar(self, tela):
        pygame.draw.rect(tela, VERDE_DRAGAO, self.rect, border_radius=20)
        pygame.draw.rect(tela, VERDE_DRAGAO, (self.rect.left - 20, self.rect.centery - 25, 40, 40), border_radius=10)
        pygame.draw.circle(tela, VERMELHO_VIDA, (self.rect.left - 5, self.rect.centery - 10), 5)
        pygame.draw.polygon(tela, CINZA_ESCURO, [(self.rect.right, self.rect.top + 20), (self.rect.right + 40, self.rect.top), (self.rect.right, self.rect.top + 50)])
        if self.hp > 0:
            barra_fundo_rect = pygame.Rect(self.rect.x, self.rect.y - 20, self.rect.width, 15)
            barra_vida_rect = pygame.Rect(self.rect.x, self.rect.y - 20, self.rect.width * (self.hp / self.hp_max), 15)
            pygame.draw.rect(tela, CINZA_ESCURO, barra_fundo_rect, border_radius=3)
            pygame.draw.rect(tela, VERMELHO_VIDA, barra_vida_rect, border_radius=3)

class Projetil(pygame.sprite.Sprite):
    def __init__(self, x, y): super().__init__(); self.rect = pygame.Rect(x, y, 20, 15); self.velocidade = -7
    def update(self): self.rect.x += self.velocidade; self.kill() if self.rect.right < 0 else None
    def desenhar(self, tela): pygame.draw.ellipse(tela, VERMELHO_COKE, self.rect); pygame.draw.circle(tela, AMARELO_CHIPS, self.rect.center, 5)

class Plataforma(pygame.sprite.Sprite):
    def __init__(self, x, y, largura, altura): super().__init__(); self.rect = pygame.Rect(x, y, largura, altura)
    def desenhar(self, tela): pygame.draw.rect(tela, VERDE_GRAMA, (self.rect.x, self.rect.y, self.rect.width, 20)); pygame.draw.rect(tela, MARROM_TERRA, (self.rect.x, self.rect.y + 20, self.rect.width, self.rect.height - 20))

class Objetivo(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo='coke'):
        super().__init__(); self.tipo = tipo
        if self.tipo == 'coke': self.rect = pygame.Rect(x, y, 25, 60)
        else: self.rect = pygame.Rect(x, y, 40, 50)
    def desenhar(self, tela):
        if self.tipo == 'coke':
            pygame.draw.rect(tela, VERMELHO_COKE, self.rect, border_radius=5); pygame.draw.rect(tela, BRANCO, (self.rect.x, self.rect.y + 15, self.rect.width, 15)); pygame.draw.line(tela, VERMELHO_COKE, (self.rect.x + 3, self.rect.y + 22), (self.rect.right - 3, self.rect.y + 22), 3); pygame.draw.rect(tela, PRETO, (self.rect.x + 5, self.rect.y - 5, self.rect.width - 10, 5))
        else:
            pygame.draw.rect(tela, AMARELO_CHIPS, self.rect, border_radius=8)
            texto_surf = FONTE_PADRAO.render("Chips", True, PRETO)
            tela.blit(texto_surf, (self.rect.centerx - texto_surf.get_width()/2, self.rect.centery - texto_surf.get_height()/2))

class Botao:
    def __init__(self, x, y, largura, altura, texto, cor_fundo, cor_hover): self.rect = pygame.Rect(x, y, largura, altura); self.texto, self.cor_fundo, self.cor_hover, self.cor_atual = texto, cor_fundo, cor_hover, cor_fundo
    def desenhar(self, tela):
        pygame.draw.rect(tela, self.cor_atual, self.rect, border_radius=10)
        texto_surf = FONTE_MENU.render(self.texto, True, BRANCO)
        tela.blit(texto_surf, (self.rect.centerx - texto_surf.get_width()/2, self.rect.centery - texto_surf.get_height()/2))
    def checar_hover(self, pos_mouse): self.cor_atual = self.cor_hover if self.rect.collidepoint(pos_mouse) else self.cor_fundo
    def checar_clique(self, pos_mouse): return self.rect.collidepoint(pos_mouse)

# --- Dados dos Níveis ---
niveis_data = {
    1: {"jogador_pos": (100, ALTURA_TELA-150), "ceu": AZUL_CEU_DIA, "plataformas": [(0, ALTURA_TELA-40, LARGURA_TELA, 40), (200, ALTURA_TELA-150, 150, 80), (450, ALTURA_TELA-250, 120, 80), (250, ALTURA_TELA-380, 100, 80), (600, ALTURA_TELA-400, 180, 80)], "inimigos": [(500, ALTURA_TELA-90), (650, ALTURA_TELA-450)], "objetivo": {"pos": (700, ALTURA_TELA-460), "tipo": "coke"}},
    2: {"jogador_pos": (50, ALTURA_TELA-100), "ceu": AZUL_CEU_NOITE, "plataformas": [(0, ALTURA_TELA-40, 250, 40), (350, ALTURA_TELA-120, 150, 40), (150, ALTURA_TELA-220, 100, 40), (400, ALTURA_TELA-300, 200, 40), (50, ALTURA_TELA-400, 150, 40), (600, ALTURA_TELA-450, LARGURA_TELA-600, 40)], "inimigos": [(400, ALTURA_TELA-170), (200, ALTURA_TELA-270), (100, ALTURA_TELA-450)], "objetivo": {"pos": (720, ALTURA_TELA-510), "tipo": "coke"}},
    "boss": {"jogador_pos": (100, ALTURA_TELA-100), "ceu": AZUL_CEU_NOITE, "plataformas": [(0, ALTURA_TELA-40, LARGURA_TELA, 40)], "inimigos": [], "boss": (600, ALTURA_TELA / 2 - 100), "objetivo": None}
}
# --- Variáveis Globais ---
jogador, objetivo, boss, balao_fala_ativo = None, None, None, None

# --- Funções do Jogo ---
def carregar_nivel(id_nivel):
    global jogador, objetivo, boss, balao_fala_ativo
    for sprite in todos_os_sprites: sprite.kill()
    boss, balao_fala_ativo = None, None
    data = niveis_data[id_nivel]

    if id_nivel == "boss": tocar_musica(MUSICA_CHEFE)
    else: tocar_musica(MUSICA_FASE)
    
    jogador = Jogador(*data["jogador_pos"])
    todos_os_sprites.add(jogador)
    for p_info in data["plataformas"]:
        p = Plataforma(*p_info)
        todos_os_sprites.add(p); plataformas_grupo.add(p)
    for i_info in data["inimigos"]:
        i = Inimigo(*i_info)
        todos_os_sprites.add(i); inimigos_grupo.add(i)
    if data.get("boss"): boss = DragaoBoss(*data["boss"]); todos_os_sprites.add(boss)
    if data.get("objetivo"): obj_data = data["objetivo"]; objetivo = Objetivo(obj_data["pos"][0], obj_data["pos"][1], obj_data["tipo"]); todos_os_sprites.add(objetivo)
    else: objetivo = None
    if id_nivel == 1: balao_fala_ativo = BalaoDeFala("Preciso da minha Coca-Cola!", 5)
    elif id_nivel == "boss": balao_fala_ativo = BalaoDeFala("Agora, as batatinhas!", 5)

def desenhar_tela(estado_jogo, nivel_atual):
    cor_ceu = niveis_data.get(nivel_atual, {}).get("ceu", AZUL_CEU_DIA)
    TELA.fill(cor_ceu)
    for p in plataformas_grupo: p.desenhar(TELA)
    for i in inimigos_grupo: i.desenhar(TELA)
    for proj in projeteis_grupo: proj.desenhar(TELA)
    if objetivo: objetivo.desenhar(TELA)
    if boss: boss.desenhar(TELA)
    if jogador: jogador.desenhar(TELA)
    if balao_fala_ativo: balao_fala_ativo.desenhar(TELA)
    if estado_jogo == "GAME_OVER":
        texto_surf = pygame.font.SysFont('Consolas', 60, bold=True).render("GAME OVER", True, VERMELHO_COKE)
        TELA.blit(texto_surf, (LARGURA_TELA/2 - texto_surf.get_width()/2, ALTURA_TELA/2 - 50))
        texto_reiniciar = FONTE_PADRAO.render("[Pressione R para voltar ao Menu]", True, BRANCO)
        TELA.blit(texto_reiniciar, (LARGURA_TELA/2 - texto_reiniciar.get_width()/2, ALTURA_TELA/2 + 20))
    pygame.display.flip()

def desenhar_menu():
    for i in range(ALTURA_TELA):
        cor = (max(0, 135 - i//6), max(0, 206 - i//4), 250)
        pygame.draw.line(TELA, cor, (0, i), (LARGURA_TELA, i))
    titulo_texto = "TBH Criatura: O Jogo"
    x_inicial = LARGURA_TELA/2 - (len(titulo_texto) * 20) / 2
    for i, char in enumerate(titulo_texto):
        cor = CORES_ARCOIRIS[i % len(CORES_ARCOIRIS)]
        texto_surf = FONTE_TITULO.render(char, True, cor)
        TELA.blit(texto_surf, (x_inicial + i * 20, 100))
    creditos_surf = FONTE_CREDITOS.render("Criado por Carlos Eduardo Correa Queiroz", True, BRANCO)
    TELA.blit(creditos_surf, (LARGURA_TELA/2 - creditos_surf.get_width()/2, 200))
    botao_iniciar.desenhar(TELA); botao_sair.desenhar(TELA)
    pygame.display.flip()

def desenhar_cutscene_final():
    TELA.fill(AZUL_CEU_DIA)
    pygame.draw.rect(TELA, AMARELO_JOINHA, (350, 200, 100, 150), border_radius=20)
    pygame.draw.rect(TELA, AMARELO_JOINHA, (320, 180, 60, 80), border_radius=20)
    parabens_surf = pygame.font.SysFont('Consolas', 48, bold=True).render("Parabens Especial!", True, BRANCO)
    TELA.blit(parabens_surf, (LARGURA_TELA/2 - parabens_surf.get_width()/2, 100))
    obrigado_surf = FONTE_MENU.render("Obrigado por jogar meu jogo", True, PRETO)
    TELA.blit(obrigado_surf, (LARGURA_TELA/2 - obrigado_surf.get_width()/2, 400))
    autor_surf = FONTE_PADRAO.render("- Carlos Eduardo Correa Queiroz", True, PRETO)
    TELA.blit(autor_surf, (LARGURA_TELA/2 - autor_surf.get_width()/2, 450))
    instrucao_surf = FONTE_PADRAO.render("[Pressione E para voltar ao Menu]", True, CINZA_ESCURO)
    TELA.blit(instrucao_surf, (LARGURA_TELA/2 - instrucao_surf.get_width()/2, 550))
    pygame.display.flip()

# --- Loop Principal ---
def main():
    global estado_jogo, nivel_atual, jogador, objetivo, boss, botao_iniciar, botao_sair, balao_fala_ativo
    estado_jogo, nivel_atual, rodando = "MENU", 1, True
    botao_iniciar = Botao(LARGURA_TELA/2 - 125, 300, 250, 60, "Iniciar Jogo", CINZA_ESCURO, CINZA_CLARO)
    botao_sair = Botao(LARGURA_TELA/2 - 125, 400, 250, 60, "Sair", VERMELHO_COKE, (255, 80, 100))
    
    tocar_musica(MUSICA_MENU)

    while rodando:
        RELÓGIO.tick(FPS)
        pos_mouse = pygame.mouse.get_pos()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: rodando = False
            if estado_jogo == "MENU":
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if botao_iniciar.checar_clique(pos_mouse):
                        nivel_atual = 1; carregar_nivel(nivel_atual); estado_jogo = "JOGANDO"
                    if botao_sair.checar_clique(pos_mouse): rodando = False
            elif estado_jogo in ["GAME_OVER", "CUTSCENE_FINAL"]:
                if evento.type == pygame.KEYDOWN and (evento.key == pygame.K_r or evento.key == pygame.K_e):
                    estado_jogo = "MENU"; tocar_musica(MUSICA_MENU)

        if estado_jogo == "MENU":
            botao_iniciar.checar_hover(pos_mouse); botao_sair.checar_hover(pos_mouse); desenhar_menu()
        elif estado_jogo == "JOGANDO":
            if balao_fala_ativo and not balao_fala_ativo.update(jogador.rect): balao_fala_ativo = None
            inimigos_grupo.update(); projeteis_grupo.update();
            if boss: boss.update()
            if jogador.mover() == "GAME_OVER":
                estado_jogo = "GAME_OVER"; pygame.mixer.music.stop(); continue
            
            colisoes_inimigos = pygame.sprite.spritecollide(jogador, inimigos_grupo, False)
            for inimigo in colisoes_inimigos:
                if jogador.vel_y > 0 and jogador.rect.bottom < inimigo.rect.centery + 10:
                    inimigo.kill(); jogador.vel_y = -8
                elif jogador.imune_timer == 0: estado_jogo = "GAME_OVER"; pygame.mixer.music.stop()
            
            if boss and jogador.rect.colliderect(boss.rect):
                if jogador.vel_y > 0 and jogador.rect.bottom < boss.rect.centery:
                    if boss.tomar_dano(): boss = None; objetivo = Objetivo(LARGURA_TELA - 100, ALTURA_TELA - 90, 'chips'); todos_os_sprites.add(objetivo)
                    jogador.vel_y = -12; jogador.imune_timer = 30
                elif jogador.imune_timer == 0: estado_jogo = "GAME_OVER"; pygame.mixer.music.stop()

            if pygame.sprite.spritecollide(jogador, projeteis_grupo, True) and jogador.imune_timer == 0:
                estado_jogo = "GAME_OVER"; pygame.mixer.music.stop()

            if objetivo and jogador.rect.colliderect(objetivo.rect):
                if nivel_atual == 1: nivel_atual = 2; carregar_nivel(nivel_atual)
                elif nivel_atual == 2: nivel_atual = "boss"; carregar_nivel(nivel_atual)
                elif nivel_atual == "boss": estado_jogo = "CUTSCENE_FINAL"; tocar_musica(MUSICA_MENU)
            
            desenhar_tela(estado_jogo, nivel_atual)
        elif estado_jogo == "GAME_OVER": desenhar_tela(estado_jogo, nivel_atual)
        elif estado_jogo == "CUTSCENE_FINAL": desenhar_cutscene_final()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()