-- SPDX-License-Identifier: MIT
-- DoD Fighter — side walls of our stages. The engine stops fighters only at x 0
-- and the stage width, where half the sprite is off-screen (and, on our
-- painted stages, standing in the scenery); these stop them further in.
-- Stage-mode enemies are left alone: they spawn off-screen and walk in.

local WALLS = {
    ["mods/darthnox/bg/bridge.txt"] = {60, 734},    -- Urban Bridge: the concrete barriers
    ["mods/darthnox/bg/roof.txt"] = {90, 1749},     -- Sunset Rooftop: the side buildings and plants
    ["mods/darthnox/bg/roofn.txt"] = {50, 863},     -- Rooftop at Night (stage 1-5): the rubble at both ends
}

return function(base)
    local background = require("base/game/background")
    local constants = require("base/game/constants")
    local record_kinds, enemies = constants.record_kinds, constants.teams.enemies
    local step = base.step
    local loaded = {}

    local function walls(stage)
        for path, pair in pairs(WALLS) do
            loaded[path] = loaded[path] or background.load(path)
            if stage == loaded[path] then return pair end
        end
    end

    function base.step(state)
        local pair = state.stage and walls(state.stage)
        if pair then
            local left, right = pair[1], pair[2]
            for index = 0, 19 do
                local value = state.items[index]
                if value and value.record.kind == record_kinds.character and value.team ~= enemies then
                    if value.x < left then value.x = left end
                    if value.x > right then value.x = right end
                end
            end
        end
        return step(state)
    end

    return base
end
