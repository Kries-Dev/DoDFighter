-- SPDX-License-Identifier: MIT
-- DoD Fighter — menu music. Every menu (launch, title, character select,
-- options) asks for LF2's bgm/main.wma; ours plays instead: "SFA MAX", the
-- user's menu track (assets/bg/menu.wma). Going from one menu to the next keeps
-- it playing instead of starting it over. Match and stage music are unchanged.

local LF2_MENU = "bgm/main.wma"
local MENU_TRACK = "mods/darthnox/bg/menu.wma"

return function(base)
    local play, stop = base.play, base.stop
    local current
    function base.play(path)
        local wanted = (path:gsub("\\", "/"):lower())
        if wanted == LF2_MENU then wanted = MENU_TRACK end
        if wanted == MENU_TRACK and current == MENU_TRACK and not base.stopped then return end
        current = wanted
        return play(wanted)
    end
    function base.stop()
        current = nil
        return stop()
    end
    return base
end
