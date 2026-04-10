extends CharacterBody2D

@onready var animated_sprite_2d: AnimatedSprite2D = $AnimatedSprite2D
@onready var collision_shape_2d: CollisionShape2D = $CollisionShape2D

const SPEED = 100.0
const JUMP_VELOCITY = 300.0
const JUMP_FORWARD_OFFSET = 54.0

enum State {
    STAND,
    WALK,
    TURN,
    JUMP_START,
    JUMP,
    JUMP_END,
    JUMP_FORWARD_START,
    JUMP_FORWARD,
    JUMP_FORWARD_END
}

var current_state: State = State.STAND
var just_entered_jump: bool = false
var turn_reverse: bool = false
var original_collision_shape_position: Vector2 = Vector2.ZERO
var original_collision_shape_size: Vector2 = Vector2.ZERO

func _ready() -> void:
    original_collision_shape_position = collision_shape_2d.position

    var collision_rect := collision_shape_2d.shape as RectangleShape2D
    if collision_rect != null:
        original_collision_shape_size = collision_rect.size

    change_state(State.STAND)
    animated_sprite_2d.connect("animation_finished", _on_AnimatedSprite2D_animation_finished)

func _physics_process(delta: float) -> void:
    # Gravity
    if not is_on_floor():
        velocity += get_gravity() * delta

    # Input
    var direction := Input.get_axis("ui_left", "ui_right")
    if current_state == State.STAND:
        if Input.is_action_just_pressed("ui_accept"):
            change_state(State.JUMP_START)
    if current_state == State.WALK:
        if Input.is_action_just_pressed("ui_accept") && direction_match_orientation(direction):
            change_state(State.JUMP_FORWARD_START)
    if current_state == State.JUMP_START:
        if direction_match_orientation(direction):
            change_state(State.JUMP_FORWARD_START)
    
                
    # State logic
    match current_state:
        State.STAND:
            velocity.x = direction * SPEED if direction != 0 else move_toward(velocity.x, 0, SPEED)
            if direction != 0:
                if not direction_match_orientation(direction):
                    # Direction opposite - need to turn
                    change_state(State.TURN)
                else:
                    change_state(State.WALK)
        State.WALK:
            if direction == 0:
                change_state(State.STAND)
            elif not direction_match_orientation(direction):
                # Direction opposite - need to turn
                change_state(State.TURN)
            else:
                velocity.x = direction * SPEED
        State.JUMP:
            if just_entered_jump:
                just_entered_jump = false
            elif is_on_floor():
                change_state(State.JUMP_END)
        State.JUMP_FORWARD:
            if just_entered_jump:
                just_entered_jump = false
            elif is_on_floor():
                change_state(State.JUMP_FORWARD_END)

    move_and_slide()

func direction_match_orientation(direction: float) -> bool:
    if animated_sprite_2d.flip_h:
        return direction < 0
    else:
        return direction > 0

func change_state(new_state: State) -> void:
    current_state = new_state
    match current_state:
        State.STAND:
            animated_sprite_2d.play("stand")
            _set_sprite_position(Vector2(0, -39))
        State.WALK:
            animated_sprite_2d.play("walk")
            animated_sprite_2d.frame = 10
            _set_sprite_position(Vector2(3, -37))
        State.TURN:
            velocity.x = 0
            animated_sprite_2d.play("turn")
            _set_sprite_position(Vector2(0, -39))
            turn_reverse = false
        State.JUMP_START:
            animated_sprite_2d.play("jump_start")
            _set_sprite_position(Vector2(3.5, -50.5))
        State.JUMP:
            animated_sprite_2d.play("jump")
            velocity.y = - JUMP_VELOCITY
            just_entered_jump = true
            _set_sprite_position(Vector2(3.5, -50.5))
        State.JUMP_END:
            animated_sprite_2d.play_backwards("jump_start")
            _set_sprite_position(Vector2(3.5, -50.5))
        State.JUMP_FORWARD_START:
            velocity.x = 0
            _extend_collision_for_jump_forward()
            animated_sprite_2d.play("jump_forward_start")
            _set_sprite_position(Vector2(22, -38))
        State.JUMP_FORWARD:
            animated_sprite_2d.play("jump_forward")
            if animated_sprite_2d.flip_h:
                velocity = Vector2(-1, -1).normalized() * JUMP_VELOCITY
            else:
                velocity = Vector2(1, -1).normalized() * JUMP_VELOCITY
            just_entered_jump = true
            _set_sprite_position(Vector2(22, -38))
        State.JUMP_FORWARD_END:
            animated_sprite_2d.play("jump_forward_end")
            velocity.x = 0
            _set_sprite_position(Vector2(22, -38))

func _set_sprite_position(base_position: Vector2) -> void:
    var pos := base_position
    if animated_sprite_2d.flip_h:
        pos.x *= -1
    animated_sprite_2d.position = pos

func _extend_collision_for_jump_forward() -> void:
    var collision_rect := collision_shape_2d.shape as RectangleShape2D
    if collision_rect == null:
        return

    var direction := -1.0 if animated_sprite_2d.flip_h else 1.0
    collision_shape_2d.position = original_collision_shape_position + Vector2(direction * JUMP_FORWARD_OFFSET / 2.0, 0)
    collision_rect.size = original_collision_shape_size + Vector2(JUMP_FORWARD_OFFSET, 0)

func _reset_collision_shape() -> void:
    var collision_rect := collision_shape_2d.shape as RectangleShape2D
    if collision_rect == null:
        return

    collision_shape_2d.position = original_collision_shape_position
    collision_rect.size = original_collision_shape_size

func _on_AnimatedSprite2D_animation_finished() -> void:
    match current_state:
        State.TURN:
            animated_sprite_2d.flip_h = !animated_sprite_2d.flip_h
            change_state(State.STAND)
        State.JUMP_START:
            change_state(State.JUMP)
        State.JUMP_END:
            change_state(State.STAND)
        State.JUMP_FORWARD_START:
            change_state(State.JUMP_FORWARD)
        State.JUMP_FORWARD_END:
            _reset_collision_shape()

            if animated_sprite_2d.flip_h:
                position.x -= JUMP_FORWARD_OFFSET
            else:
                position.x += JUMP_FORWARD_OFFSET

            change_state(State.STAND)
