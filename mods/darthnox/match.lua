-- SPDX-License-Identifier: MIT
-- DoD Fighter — low defence: DarthNox takes 10% more damage, Mathilde 25% (the
-- engine divides every hit by armor/100, and battle mode's defence setting
-- is scaled the same way). Also: Urban Bridge plays its own track ("Gravity Stars") instead of the
-- Versus music pick. Music set to OFF stays off, and the title-screen demo keeps
-- its own music.

-- armor multipliers: damage taken is x 100/armor, so 0.91 = +10%, 0.80 = +25%
local DEFENCE = {[61] = 0.91, [63] = 0.80}   -- DarthNox, Mathilde

return function(base)
    local stage_path = "mods/darthnox/bg/bridge.txt"
    local track = "mods/darthnox/bg/gravity_stars.wma"
    local background = require("base/game/background")
    local music = require("base/game/music")
    local create = base.create

    function base.create(options)
        local state = create(options)
        if state and state.items then
            for index = 0, 19 do
                local value = state.items[index]
                local defence = value and DEFENCE[value.record.id]
                if defence then
                    value.armor = math.floor((value.armor > 0 and value.armor or 100) * defence)
                end
            end
        end
        if state and state.stage == background.load(stage_path) and not options.demo then
            music.play(track)
        end
        return state
    end

    return base
end
