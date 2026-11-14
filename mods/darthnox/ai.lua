-- SPDX-License-Identifier: MIT
-- DoD Fighter — computer control for our fighters' special moves.
--
-- The base AI (base/game/ai.lua) only knows the stock fighters' specials, by
-- record id; DarthNox (61) and Mathilde (63) got just the generic walking,
-- punching and jumping. After the base AI has picked its keys for one of them,
-- this may start one of their moves instead, the same way the base AI does
-- (marking a D-direction-A/J sequence complete, so the frame's hit_ field
-- takes it), or press A/J to continue a move that has follow-ups.
--
-- Each rule has a range check (x and z distance to the nearest enemy), an MP
-- check and a per-tick chance; harder difficulties use them more often. The
-- chances are per tick (30 a second), so they are small.

local constants = require("base/game/constants")
local combo = constants.combo_indices
local complete = constants.combo_states.complete
local kinds = constants.record_kinds
local states = constants.frame_states

local DARTHNOX, MATHILDE = 61, 63
local FACING_RIGHT = 0

local function random(range) return engine.random(range) end
local function chance(n, skill) return random(math.max(2, n - skill * 4)) == 0 end

local function state_of(value) return value.record.frame(value.frame).state end

-- Standing, walking or in the defend stance: frames that carry the hit_ fields.
local function ready(S)
    return S.frame <= 8 or S.frame == 110
end

local function nearest_enemy(state, S)
    local best, best_d
    for index = 0, constants.item_slots - 1 do
        local T = state.items[index]
        if T and T ~= S and T.record.kind == kinds.character and T.hp > 0 and T.team ~= S.team
           and T.blink == 0 then
            local d = math.abs(T.x_int - S.x_int) + 3 * math.abs(T.z_int - S.z_int)
            if not best_d or d < best_d then best, best_d = T, d end
        end
    end
    return best
end

-- A press the engine sees as new this tick.
local function tap(S, key)
    S.keys[key] = true
    S.previous_keys[key] = false
end

local function start(S, index) S.sequences[index] = complete end

-- D>A / D>J toward the target (they also turn the fighter).
local function forward(S, T, attack)
    if T.x_int >= S.x_int then start(S, attack and combo.right_attack or combo.right_jump)
    else start(S, attack and combo.left_attack or combo.left_jump) end
end

local function facing_target(S, T)
    return (S.facing == FACING_RIGHT) == (T.x_int >= S.x_int)
end

local function hurt(T)
    local s = state_of(T)
    return s == states.injured or s == states.dizzy or s == states.broken_defend or s == states.falling
end

local function darthnox(state, S, T, dx, dz, skill)
    local mp, f, ts = S.mp, S.frame, state_of(T)
    -- Flurry: mash A for more rounds while the target is still in front.
    if f >= 281 and f <= 287 then
        if dx < 70 and dz < 10 and mp >= 20 and chance(3, skill) then tap(S, "attack") end
        return
    end
    -- Lunge into the rising slash when the target ends up in the air.
    if f >= 261 and f <= 263 then
        if T.y_int < -20 and dx < 90 and mp >= 100 and chance(4, skill) then start(S, combo.up_attack) end
        return
    end
    if not ready(S) then return end
    -- Parry an attack about to land.
    if ts == states.attacking and dx < 100 and dz < 15 and mp >= 200 and facing_target(S, T) and chance(10, skill) then
        start(S, combo.jump_attack) return
    end
    if dz < 10 and dx < 70 and mp >= 50 and facing_target(S, T) and (hurt(T) and chance(6, skill) or chance(60, skill)) then
        start(S, combo.down_attack) return                                  -- flurry
    end
    if dz < 10 and dx < 90 and mp >= 100 and facing_target(S, T) and (T.y_int < -20 and chance(4, skill) or chance(35, skill)) then
        start(S, combo.up_attack) return                                    -- rising slash
    end
    if dz < 10 and dx > 70 and dx < 150 and mp >= 75 and chance(25, skill) then
        forward(S, T, false) return                                         -- lunge
    end
    if dz < 12 and dx > 150 and dx < 380 and mp >= 60 and chance(30, skill) then
        forward(S, T, true) return                                          -- crescent
    end
end

local function mathilde(state, S, T, dx, dz, skill)
    local mp, f = S.mp, S.frame
    local ahead = facing_target(S, T)
    -- D>A stab: vault after it (J) or jump into the air extension (DJA).
    if f >= 236 and f <= 239 then
        if ahead and dx < 170 and dz < 15 and hurt(T) and mp >= 20 and chance(3, skill) then tap(S, "jump")
        elseif ahead and dx > 90 and dx < 220 and dz < 15 and chance(3, skill) then start(S, combo.jump_attack) end
        return
    end
    -- Vaults: the launcher strike when over the target, then maybe vault 2.
    if (f >= 240 and f <= 244) or (f >= 290 and f <= 294) then
        if dx < 110 and dz < 20 and chance(3, skill) then tap(S, "attack") end
        return
    end
    if f >= 300 and f <= 303 then
        if T.y_int < -20 and dx < 160 and mp >= 20 and chance(4, skill) then tap(S, "jump") end
        return
    end
    if not ready(S) then return end
    if dz < 10 and dx < 70 and mp >= 40 and ahead and (hurt(T) and chance(6, skill) or chance(60, skill)) then
        start(S, combo.down_attack) return                                  -- staff combo
    end
    if dz < 12 and dx > 80 and dx < 200 and mp >= 50 and chance(25, skill) then
        forward(S, T, true) return                                          -- staff extension
    end
    if dz < 20 and dx > 60 and dx < 220 and mp >= 200 and ahead and chance(40, skill) then
        start(S, combo.up_jump) return                                      -- tornado
    end
    if dx > 200 and dz < 80 and mp >= 75 and ahead and chance(45, skill) then
        start(S, combo.up_attack) return                                    -- homing staff
    end
    if not S.dod_clone and mp >= 300 and dx > 100 and chance(60, skill) then
        start(S, combo.down_jump) return                                    -- clone
    end
end

return function(base)
    local control = base.control

    function base.control(state, index, mode, context)
        local result = control(state, index, mode, context)
        local S = state.items[index]
        local id = S and S.record.id
        if (id == DARTHNOX or id == MATHILDE) and S.hp > 0 and not S.human then
            local T = nearest_enemy(state, S)
            if T then
                local dx, dz = math.abs(T.x_int - S.x_int), math.abs(T.z_int - S.z_int)
                local skill = math.max(0, state.ai_skill or 0)
                if id == DARTHNOX then darthnox(state, S, T, dx, dz, skill)
                else mathilde(state, S, T, dx, dz, skill) end
            end
        end
        return result
    end

    return base
end
