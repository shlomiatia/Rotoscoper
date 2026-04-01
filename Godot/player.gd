extends CharacterBody2D

@onready var animated_sprite_2d: AnimatedSprite2D = $AnimatedSprite2D

const SPEED = 100.0
const JUMP_VELOCITY = -400.0

enum State {
    STAND,
    START_WALK,
    WALK,
    TURN,
    JUMP_START,
    JUMP,
    JUMP_END
}

var current_state: State = State.STAND
var just_entered_jump: bool = false
var turn_reverse: bool = false

func _physics_process(delta: float) -> void:
    # Gravity
    if not is_on_floor():
        velocity += get_gravity() * delta

    # Input
    var direction := Input.get_axis("ui_left", "ui_right")
    if Input.is_action_just_pressed("ui_accept") and current_state == State.STAND:
        change_state(State.JUMP_START)

    # State logic
    match current_state:
        State.STAND:
            velocity.x = direction * SPEED if direction != 0 else move_toward(velocity.x, 0, SPEED)
            if direction != 0:
                if animated_sprite_2d.flip_h != (direction < 0):
                    # Direction opposite - need to turn
                    change_state(State.TURN)
                else:
                    change_state(State.START_WALK)
        State.START_WALK:
            velocity.x = direction * SPEED
            if direction == 0:
                change_state(State.STAND)
        State.WALK:
            if direction == 0:
                change_state(State.STAND)
            elif animated_sprite_2d.flip_h != (direction < 0):
                # Direction opposite - need to turn
                change_state(State.TURN)
            else:
                velocity.x = direction * SPEED
        State.JUMP_START:
            pass # Wait for animation
        State.JUMP:
            if just_entered_jump:
                just_entered_jump = false
            elif is_on_floor():
                change_state(State.JUMP_END)
        State.JUMP_END:
            pass # Wait for animation

    move_and_slide()

func change_state(new_state: State) -> void:
    # Exit current state if needed
    # (none for now)
    # Enter new state
    current_state = new_state
    match current_state:
        State.STAND:
            animated_sprite_2d.play("stand")
            animated_sprite_2d.position = Vector2(-5, 0)
        State.START_WALK:
            animated_sprite_2d.play("start_walk")
            animated_sprite_2d.position = Vector2(-5, 0)
        State.WALK:
            animated_sprite_2d.play("walk")
            animated_sprite_2d.position = Vector2(-5, 0)
        State.TURN:
            velocity.x = 0
            animated_sprite_2d.play("turn")
            animated_sprite_2d.position = Vector2(1, 0)
            turn_reverse = false
        State.JUMP_START:
            animated_sprite_2d.play("jump_start")
            animated_sprite_2d.position = Vector2(5, -10)
        State.JUMP:
            animated_sprite_2d.play("jump")
            velocity.y = JUMP_VELOCITY
            just_entered_jump = true
            animated_sprite_2d.position = Vector2(5, -10)
        State.JUMP_END:
            animated_sprite_2d.play_backwards("jump_start")
            animated_sprite_2d.position = Vector2(5, -10)

func _ready() -> void:
    animated_sprite_2d.connect("animation_finished", _on_AnimatedSprite2D_animation_finished)

func _on_AnimatedSprite2D_animation_finished() -> void:
    match current_state:
        State.START_WALK:
            if animated_sprite_2d.animation == "start_walk":
                change_state(State.WALK)
        State.TURN:
            if not turn_reverse:
                # Play turn animation in reverse
                turn_reverse = true
                animated_sprite_2d.flip_h = !animated_sprite_2d.flip_h
                animated_sprite_2d.play_backwards("turn")
            else:
                # Turn complete, return to stand
                change_state(State.STAND)
        State.JUMP_START:
            if animated_sprite_2d.animation == "jump_start":
                change_state(State.JUMP)
        State.JUMP_END:
            if animated_sprite_2d.animation == "jump_start":
                change_state(State.STAND)
