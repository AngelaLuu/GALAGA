from machine import Pin, ADC, I2C, PWM
import ssd1306
import neopixel
import time
import random

# Inicializar I2C para la pantalla OLED
i2c = I2C(0, scl=Pin(33), sda=Pin(32))
oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Configurar joystick
#disparar_btn = ADC(Pin(12))  # Leer eje Y del joystick para disparar
joy_x = ADC(Pin(34))
joy_x.atten(ADC.ATTN_11DB)
#disparar_btn.atten(ADC.ATTN_11DB) 

# Configuración del juego
WIDTH, HEIGHT = 128, 64
player_x = WIDTH // 2  # Posición inicial del jugador
player_speed = 2
objects = []  # Lista de enemigos
bullets = []  # Lista de disparos
score = 0  # Puntuación
lives = 3  # Vidas del jugador
shoot_timer = 0  # Temporizador para disparo automático

# Configuración del NeoPixel (con 3 LEDs) en el pin 12
np = neopixel.NeoPixel(Pin(15), 3)

# Configuración del buzzer en el pin 34
buzzer = PWM(Pin(2))

# Notas musicales (frecuencia en Hz)
NOTES = {
    "C5": 523, "D5": 587, "E5": 659, "G5": 784, "A5": 880,  # Notas agudas
    "C4": 261, "E4": 330, "G4": 392  # Notas más graves
}

# Función para hacer sonar el buzzer
def play_tone(frequency, duration):
    buzzer.freq(frequency)
    buzzer.duty(512)  # Volumen del sonido
    time.sleep(duration)
    buzzer.duty(0)  # Apagar el sonido
    time.sleep(0.05)

# Melodía de inicio del juego
def play_start_melody():
    melody = [("C5", 0.2), ("E5", 0.2), ("G5", 0.2), ("C5", 0.3)]
    for note, duration in melody:
        play_tone(NOTES[note], duration)

# Sonido al perder una vida
def play_death_sound():
    death_melody = [("G4", 0.2), ("E4", 0.2), ("C4", 0.3)]
    for note, duration in death_melody:
        play_tone(NOTES[note], duration)

# Sonido de "Game Over"
def play_game_over_sound():
    game_over_melody = [("C4", 0.3), ("G4", 0.3), ("E4", 0.4)]
    for note, duration in game_over_melody:
        play_tone(NOTES[note], duration)

def update_neopixel():
    """Actualiza los LEDs del NeoPixel según las vidas restantes."""
    for i in range(3):
        if i < lives:
            np[i] = (0, 255, 0)  # Verde si tiene vidas
        else:
            np[i] = (0, 0, 0)  # Apagado si perdió la vida
    np.write()

# Reproducir melodía de inicio al encender el juego
play_start_melody()
update_neopixel()

# Crear estrellas de fondo
stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT)] for _ in range(10)]

def draw_game():
    """Dibuja el juego en la pantalla OLED"""
    global player_x, score, lives
    oled.fill(0)

    # Dibujar estrellas
    for star in stars:
        star[1] += 1
        if star[1] > HEIGHT:
            star[0] = random.randint(0, WIDTH)
            star[1] = 0
        oled.pixel(star[0], star[1], 1)
    
    # Dibujar enemigos
    for obj in objects:
        obj[1] += 2  # Mover los enemigos hacia abajo
        if obj[1] > HEIGHT:
            obj[0] = random.randint(0, WIDTH)
            obj[1] = 0
        oled.fill_rect(obj[0], obj[1], 5, 5, 1)  # Dibujar enemigos
    
    # Dibujar disparos
    for bullet in bullets:
        bullet[1] -= 3  # Mover hacia arriba
        oled.rect(bullet[0], bullet[1], 2, 5, 1)
    
    # Detectar colisiones entre disparos y enemigos
    for bullet in bullets[:]:
        for obj in objects[:]:
            if bullet[0] in range(obj[0], obj[0] + 5) and bullet[1] in range(obj[1], obj[1] + 5):
                objects.remove(obj)
                bullets.remove(bullet)
                score += 1
                break
    
    # Detectar colisión entre jugador y enemigos
    for obj in objects[:]:
        if obj[1] >= HEIGHT - 10 and obj[0] in range(player_x, player_x + 10):
            lives -= 1
            objects.remove(obj)
            update_neopixel()  # Actualizar los LEDs del NeoPixel
            play_death_sound()  # Reproducir sonido de muerte
            
            if lives == 0:
                oled.fill(0)
                oled.text("GAME OVER", 35, 30)
                oled.show()
                play_game_over_sound()  # Sonido de "Game Over"
                time.sleep(2)
                np.fill((0, 0, 0))  # Apagar todos los LEDs en "GAME OVER"
                np.write()
                return False  # Terminar el juego

    # Dibujar jugador (nave)
    oled.rect(player_x, HEIGHT - 10, 10, 5, 1)
    
    # Mostrar puntuación y vidas
    oled.text(f"Score: {score}", 2, 2)
    oled.text(f"Lives: {lives}", 2, 12)
    
    oled.show()
    return True

# Crear enemigos iniciales
for _ in range(5):
    objects.append([random.randint(0, WIDTH), random.randint(0, HEIGHT // 2)])

while True:
    # Leer valores del joystick
    x_value = joy_x.read()
    
    if x_value > 3000:
        player_x = max(0, player_x - player_speed)
    elif x_value <1000:
        player_x = min(WIDTH - 10, player_x + player_speed)
    
    # Disparo automático cada cierto tiempo
    shoot_timer += 1
    if shoot_timer > 5:
        bullets.append([player_x + 4, HEIGHT - 12])
        shoot_timer = 0
    
    
    
    # Generar nuevos enemigos constantemente
    if len(objects) < 5:
        objects.append([random.randint(0, WIDTH), 0])
    
    # Dibujar juego y verificar si sigue en ejecución
    if not draw_game():
        break

    time.sleep(0.1)
