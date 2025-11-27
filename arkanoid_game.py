"""Plantilla del juego Arkanoid para el hito M2.

Completa los métodos marcados con TODO respetando las anotaciones de tipo y la
estructura de la clase. El objetivo es construir un prototipo jugable usando
pygame que cargue bloques desde un fichero de nivel basado en caracteres.
"""
from arkanoid_core import *
# --------------------------------------------------------------------- #
# Métodos a completar por el alumnado
# --------------------------------------------------------------------- #

@arkanoid_method
def cargar_nivel(self) -> list[str]:
    """Lee el fichero de nivel y devuelve la cuadrícula como lista de filas."""
    
    # 1. Comprobamos si el fichero existe y es válido
    if not self.level_path.exists() or not self.level_path.is_file():
        raise FileNotFoundError(f"No se encuentra el nivel: {self.level_path}")

    # 2. Leemos el contenido y dividimos en líneas
    # Especificamos encoding="utf-8" para evitar problemas con caracteres extraños
    contenido = self.level_path.read_text(encoding="utf-8")
    lineas = contenido.splitlines()

    # (Opcional) Filtramos líneas totalmente vacías para evitar errores si hay saltos al final
    lineas = [l for l in lineas if l]

    if not lineas:
        raise ValueError("El fichero de nivel está vacío.")

    # 3. Validamos que todas las filas tengan el mismo ancho
    ancho_referencia = len(lineas[0])
    for i, linea in enumerate(lineas):
        if len(linea) != ancho_referencia:
            raise ValueError(
                f"El nivel no es rectangular. Línea {i} tiene longitud {len(linea)} "
                f"pero se esperaba {ancho_referencia}."
            )

    # 4. Guardamos y devolvemos
    self.layout = lineas
    return self.layout

@arkanoid_method
def preparar_entidades(self) -> None:
    """Posiciona paleta y bola, y reinicia puntuación y vidas."""
    
    # 1. Configurar la paleta (Pista: usa self.crear_rect)
    # Creamos el rectángulo con las dimensiones del core (120x18)
    # Inicialmente en (0,0) porque luego lo moveremos.
    self.paddle = self.crear_rect(0, 0, *self.PADDLE_SIZE)

    # 2. Centrar la paleta en la parte inferior
    # Calculamos el centro horizontal de la pantalla
    centro_x = self.SCREEN_WIDTH // 2
    # Calculamos la posición vertical restando el margen (OFFSET) al alto total
    pos_y = self.SCREEN_HEIGHT - self.PADDLE_OFFSET
    
    # Usamos la propiedad 'midbottom' de pygame para centrarlo fácilmente
    self.paddle.midbottom = (centro_x, pos_y)

    # 3. Reiniciar variables de puntuación/vidas
    self.score = 0
    self.lives = 3
    self.end_message = ""

    # 4. Preparar la bola (Pista: llama a self.reiniciar_bola())
    # Esto coloca la bola pegada encima de la paleta y resetea su Vector2
    self.reiniciar_bola()

@arkanoid_method
def crear_bloques(self) -> None:
    """Genera los rectángulos de los bloques en base a la cuadrícula."""
    
    # 1. Limpia las listas anteriores (por si recargamos el nivel)
    self.blocks = []
    self.block_colors = []
    self.block_symbols = []

    # 2. Recorre self.layout para detectar símbolos
    # Usamos 'enumerate' para tener tanto el índice (fila_idx) como el contenido
    for fila_idx, linea in enumerate(self.layout):
        for col_idx, simbolo in enumerate(linea):
            
            # 3. Verificamos si el símbolo es un bloque válido
            # Si el símbolo está en el diccionario de colores, es que es un bloque
            if simbolo in self.BLOCK_COLORS:
                
                # 4. Obtenemos el rectángulo usando el método auxiliar del core
                rect = self.calcular_posicion_bloque(fila_idx, col_idx)
                
                # 5. Rellenamos las listas paralelas
                self.blocks.append(rect)
                # Buscamos el color correspondiente al símbolo
                self.block_colors.append(self.BLOCK_COLORS[simbolo])
                self.block_symbols.append(simbolo)

@arkanoid_method
def procesar_input(self) -> None:
    """Gestiona la entrada de teclado para mover la paleta."""
    
    # 1. Obtener el estado de teclas (Pista: self.obtener_estado_teclas())
    # Devuelve una lista/diccionario donde podemos consultar si una tecla está pulsada
    keys = self.obtener_estado_teclas()

    # 2. Movimiento a la IZQUIERDA
    # Comprobamos Flecha Izquierda O tecla 'A'
    if keys[self.KEY_LEFT] or keys[self.KEY_A]:
        self.paddle.x -= self.PADDLE_SPEED

    # 3. Movimiento a la DERECHA
    # Comprobamos Flecha Derecha O tecla 'D'
    if keys[self.KEY_RIGHT] or keys[self.KEY_D]:
        self.paddle.x += self.PADDLE_SPEED

    # 4. Limitar la posición (Clamping)
    # Si la parte izquierda de la paleta se sale por la izquierda (< 0), la pegamos a 0
    if self.paddle.left < 0:
        self.paddle.left = 0
    
    # Si la parte derecha se sale por la derecha (> SCREEN_WIDTH), la pegamos al borde
    if self.paddle.right > self.SCREEN_WIDTH:
        self.paddle.right = self.SCREEN_WIDTH

@arkanoid_method
def actualizar_bola(self) -> None:
    """Actualiza la posición de la bola y resuelve colisiones."""
    
    if self.end_message:
        return

    # 1. MOVER LA BOLA
    self.ball_pos += self.ball_velocity
    ball_rect = self.obtener_rect_bola()

    # 2. REBOTES CON PAREDES
    if ball_rect.left < 0 or ball_rect.right > self.SCREEN_WIDTH:
        self.ball_velocity.x *= -1
        if ball_rect.left < 0: self.ball_pos.x = self.BALL_RADIUS
        if ball_rect.right > self.SCREEN_WIDTH: self.ball_pos.x = self.SCREEN_WIDTH - self.BALL_RADIUS

    if ball_rect.top < 0:
        self.ball_velocity.y *= -1
        self.ball_pos.y = self.BALL_RADIUS

    # 3. GESTIÓN DE VIDAS (El suelo)
    if ball_rect.top > self.SCREEN_HEIGHT:
        self.lives -= 1
        if self.lives > 0:
            self.reiniciar_bola()
        else:
            self.end_message = "GAME OVER"
        return

    # 4. COLISIÓN CON PALETA (MEJORADA - CON EFECTO)
    if ball_rect.colliderect(self.paddle):
        # Solo rebotamos si la bola está bajando
        if self.ball_velocity.y > 0:
            # Calculamos dónde golpeó relativo al centro (-1 a 1)
            diferencia_x = ball_rect.centerx - self.paddle.centerx
            ancho_mitad = self.paddle.width / 2
            factor = diferencia_x / ancho_mitad
            
            # Nueva velocidad: X depende del golpe, Y siempre hacia arriba
            nueva_velocidad = Vector2(factor * self.BALL_SPEED, -self.BALL_SPEED)
            
            # Normalizamos para mantener la velocidad constante
            self.ball_velocity = nueva_velocidad.normalize() * self.BALL_SPEED

    # 5. COLISIÓN CON BLOQUES
    indice_colision = -1
    for i, bloque in enumerate(self.blocks):
        if ball_rect.colliderect(bloque):
            indice_colision = i
            break
    
    if indice_colision != -1:
        self.ball_velocity.y *= -1
        simbolo = self.block_symbols[indice_colision]
        puntos = self.BLOCK_POINTS.get(simbolo, 10)
        self.score += puntos
        
        self.blocks.pop(indice_colision)
        self.block_colors.pop(indice_colision)
        self.block_symbols.pop(indice_colision)

    # 6. VICTORIA
    if not self.blocks:
        self.end_message = "VICTORY!"

@arkanoid_method
def dibujar_escena(self) -> None:
    """Renderiza fondo, bloques, paleta, bola y HUD."""
    
    # 0. Seguridad: Si no hay pantalla inicializada, no hacemos nada
    if not self.screen:
        return

    # 1. FONDO
    # Limpiamos el frame anterior pintando todo del color de fondo
    self.screen.fill(self.BACKGROUND_COLOR)

    # 2. BLOQUES
    # Usamos zip() para recorrer la lista de rectángulos y la de colores a la vez
    for bloque, color in zip(self.blocks, self.block_colors):
        self.dibujar_rectangulo(bloque, color)

    # 3. PALETA
    self.dibujar_rectangulo(self.paddle, self.PADDLE_COLOR)

    # 4. BOLA
    # Convertimos la posición (Vector2) a una tupla de enteros (int, int) para dibujar
    centro_bola = (int(self.ball_pos.x), int(self.ball_pos.y))
    self.dibujar_circulo(centro_bola, self.BALL_RADIUS, self.BALL_COLOR)

    # 5. HUD (Marcadores)
    # Dibujamos texto en la parte superior
    self.dibujar_texto(f"Puntuación: {self.score}", (20, 20))
    self.dibujar_texto(f"Vidas: {self.lives}", (self.SCREEN_WIDTH - 120, 20))

    # 6. MENSAJE FINAL (Victoria/Derrota)
    if self.end_message:
        # Si hay mensaje, lo mostramos en grande en el centro (aprox)
        self.dibujar_texto(self.end_message, (self.SCREEN_WIDTH // 2 - 80, self.SCREEN_HEIGHT // 2), grande=True)

@arkanoid_method
def run(self) -> None:
    """Ejecuta el bucle principal del juego."""
    
    # 1. INICIALIZACIÓN
    # Arrancamos la ventana de Pygame y el reloj
    self.inicializar_pygame()
    
    # Preparamos el nivel y los objetos llamando a los métodos que hicimos antes
    self.cargar_nivel()
    self.preparar_entidades()
    self.crear_bloques()

    # Variable de control del bucle
    self.running = True

    # 2. BUCLE PRINCIPAL (Game Loop)
    while self.running:
        
        # A) Procesar Eventos (Input del sistema)
        for event in self.iterar_eventos():
            # Si cierran la ventana (X)
            if event.type == self.EVENT_QUIT:
                self.running = False
            # (Opcional) Si pulsan ESC, también salimos
            elif event.type == self.EVENT_KEYDOWN:
                if event.key == self.KEY_ESCAPE:
                    self.running = False

        # B) Actualizar Lógica (Solo si el juego sigue en marcha)
        self.procesar_input()
        self.actualizar_bola()

        # C) Dibujar
        self.dibujar_escena()
        
        # D) Refrescar Pantalla (Hacer visibles los cambios)
        self.actualizar_pantalla()

        # E) Control de Tiempo (Mantener 60 FPS estables)
        # self.clock se inicializó en inicializar_pygame()
        if self.clock:
            self.clock.tick(self.FPS)

    # 3. CIERRE
    # Al salir del while, cerramos Pygame correctamente
    self.finalizar_pygame()


def main() -> None:
    """Permite ejecutar el juego desde la línea de comandos."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Plantilla del hito M2: Arkanoid con pygame.",
    )
    parser.add_argument(
        "level",
        type=str,
        help="Ruta al fichero de nivel (texto con # para bloques y . para huecos).",
    )
    args = parser.parse_args()

    game = ArkanoidGame(args.level)
    game.run()


if __name__ == "__main__":
    main()

