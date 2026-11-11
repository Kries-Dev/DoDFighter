-- SPDX-License-Identifier: MIT
-- DarthNox — Urban Bridge plays its own track ("Gravity Stars") instead of the
-- Versus music pick. Music set to OFF stays off, and the title-screen demo keeps
-- its own music.

return function(base)
    local stage_path = "mods/darthnox/bg/bridge.txt"
    local track = "mods/darthnox/bg/gravity_stars.wma"
    local background = require("base/game/background")
    local music = require("base/game/music")
    local create = base.create

    function base.create(options)
        local state = create(options)
        if state and state.stage == background.load(stage_path) and not options.demo then
            music.play(track)
        end
        return state
    end

    return base
end
