-- SPDX-License-Identifier: MIT
-- DoD Fighter — which items fall from the sky. The user's list: baseball bat
-- (LF2's stick, 100), baseball (121), boomerang (124), crate (wooden box, 151),
-- milk (122) and beer (123). The hoe (101), knife (120) and stone (150) are out.
-- The base drop picks any item id from the catalog; when it lands on one of
-- those, the same slot gets an allowed item instead, at the same place.
-- (Items a move spawns, like Freeze's ice sword or Louis's armour, are untouched.)

local REMOVED = {[101] = true, [120] = true, [150] = true}
local REPLACEMENTS = {100, 121, 124, 151}

return function(base)
    local constants = require("base/game/constants")
    local objects = require("base/game/objects")
    local drop_background = base.drop_background

    function base.drop_background(state)
        local before = {}
        for index = 0, constants.item_slots - 1 do before[index] = state.items[index] end
        drop_background(state)
        for index = 0, constants.item_slots - 1 do
            local value = state.items[index]
            if value and value ~= before[index] and REMOVED[value.record.id] then
                local swap = objects.place(state, index, REPLACEMENTS[engine.random(#REPLACEMENTS) + 1])
                if swap then
                    swap.x, swap.y, swap.z = value.x, value.y, value.z
                    swap.x_int, swap.y_int, swap.z_int = value.x_int, value.y_int, value.z_int
                    swap.vx, swap.vy, swap.vz = 0.0, 0.0, 0.0
                    swap.owner = value.owner
                    for other = 0, constants.item_slots - 1 do
                        local existing = state.items[other]
                        if existing then existing.pair_rest[index] = 0 end
                    end
                end
            end
        end
    end

    return base
end
