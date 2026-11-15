-- SPDX-License-Identifier: MIT
-- DoD Fighter — low defence: DarthNox takes 10% more damage, Mathilde 25% (the
-- engine divides every hit by armor/100, and battle mode's defence setting
-- is scaled the same way). Also: our stages play their own track (MUSIC) instead
-- of the Versus music pick. Music set to OFF stays off, and the title-screen demo
-- keeps its own music.

-- armor multipliers: damage taken is x 100/armor, so 0.91 = +10%, 0.80 = +25%
local DEFENCE = {[61] = 0.91, [63] = 0.80, [68] = 0.87}   -- DarthNox, Mathilde, Cod1eh

-- stage -> its music (WMA 8, tools/to_wma.ps1)
local MUSIC = {
    ["mods/darthnox/bg/bridge.txt"] = "mods/darthnox/bg/gravity_stars.wma",   -- Urban Bridge: "Gravity Stars"
    ["mods/darthnox/bg/roof.txt"] = "mods/darthnox/bg/urban_jungle.wma",      -- Sunset Rooftop: "Urban Jungle"
}

return function(base)
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
        if state and state.stage and not options.demo then
            for path, track in pairs(MUSIC) do
                if state.stage == background.load(path) then music.play(track) break end
            end
        end
        return state
    end

    return base
end
