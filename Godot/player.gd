extends CharacterBody2D

@onready var animated_sprite_2d: AnimatedSprite2D = $AnimatedSprite2D


const SPEED = 100.0
const JUMP_VELOCITY = -400.0
var is_walking: bool = false


func _physics_process(delta: float) -> void:
    if not is_on_floor():
        velocity += get_gravity() * delta

    if Input.is_action_just_pressed("ui_accept") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    var direction := Input.get_axis("ui_left", "ui_right")
    if direction != 0:
        velocity.x = direction * SPEED
        animated_sprite_2d.flip_h = direction < 0
        if !is_walking:
            animated_sprite_2d.play("start_walk")
            is_walking = true
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)
        
        if is_walking:
            animated_sprite_2d.play("stand")
            is_walking = false

    move_and_slide()


func _ready() -> void:
    animated_sprite_2d.connect("animation_finished", _on_AnimatedSprite2D_animation_finished)

func _on_AnimatedSprite2D_animation_finished() -> void:
    if animated_sprite_2d.animation == "start_walk":
        animated_sprite_2d.play("walk")
