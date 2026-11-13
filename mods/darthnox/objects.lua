-- SPDX-License-Identifier: MIT
-- DoD Fighter — Mathilde's clone (DvJ). The engine gives Rudolf's clones 10 HP
-- and 5 MP; a clone of Mathilde spawned from her frames would get her full
-- 500 HP, so it is set here to 15 HP (+50%) and 5 MP (too little to clone again).

local MATHILDE = 63
local CLONE_HP, CLONE_MP = 15, 5

return function(base)
    local spawn = base.spawn_from_frame

    function base.spawn_from_frame(state, index, parent)
        local result = spawn(state, index, parent)
        if parent and parent.record.id == MATHILDE then
            for slot = 20, 399 do
                local value = state.items[slot]
                if value and value.record.id == MATHILDE and value.follow ~= -1 and not value.dod_clone then
                    value.dod_clone = true
                    value.hp, value.max_hp, value.dark_hp, value.mp = CLONE_HP, CLONE_HP, CLONE_HP, CLONE_MP
                end
            end
        end
        return result
    end

    return base
end
