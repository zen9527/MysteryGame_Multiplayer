$ErrorActionPreference = 'Stop'

Write-Host '=== 新建测试剧本 ===' -ForegroundColor Cyan
""

$title = Read-Host '剧本标题 (默认: 测试剧本-迷雾之夜)'
if ([string]::IsNullOrWhiteSpace($title)) { $title = '测试剧本-迷雾之夜' }

""
Write-Host '可选类型: 悬疑推理 古风权谋 现代都市 恐怖惊悚 欢乐搞笑 科幻未来' -ForegroundColor DarkGray
$genre = Read-Host '剧本类型 (默认: 悬疑推理)'
if ([string]::IsNullOrWhiteSpace($genre)) { $genre = '悬疑推理' }

""
$adminKey = Read-Host '管理员密钥 (留空则仅保存到文件)'
""

$script = @{}
$script.title = $title
$script.genre = $genre
$script.difficulty = '中等'
$script.estimated_time = 90
$script.player_count = 4
$script.background_story = '暴风雪山庄内，一位富商在书房中被发现身亡。大门被暴雪封锁，所有人都被困其中，凶手就在你们中间。'
$script.true_killer = '林默'
$script.murder_method = '毒杀——毒药被下在酒杯中'
$script.cover_up = '将毒瓶藏在死者身上，伪装成自杀'

$script.roles = @()
$r1 = @{
    name = '林默'
    age = 35
    occupation = '律师'
    description = '冷静睿智的律师，是死者的私人法律顾问'
    background = '五年前曾因一起案件与死者结怨，但表面维持着良好的合作关系'
    secret_task = '销毁一份对自己不利的法律文件'
    alibi = '案发时声称在书房隔壁的会客室打电话'
    motive = '死者掌握了他伪造证据的把柄，以此威胁他'
    relationships = @(
        @{target='苏婉'; relation='青梅竹马'}
        @{target='赵铁柱'; relation='对手'}
    )
}
$script.roles += $r1

$r2 = @{
    name = '苏婉'
    age = 28
    occupation = '画家'
    description = '美丽而忧郁的女画家，死者的养女'
    background = '从小被死者收养，但死者一直控制着她的人生'
    secret_task = '找到生母留给自己的遗物'
    alibi = '案发时在画室画画，无人证明'
    motive = '发现死者侵吞了生母留给她的遗产'
    relationships = @(
        @{target='林默'; relation='青梅竹马'}
        @{target='周明远'; relation='未婚妻'}
    )
}
$script.roles += $r2

$r3 = @{
    name = '赵铁柱'
    age = 45
    occupation = '管家'
    description = '沉默寡言的老管家，在庄园工作超过二十年'
    background = '年轻时曾是死者的生意伙伴，后因破产成为管家'
    secret_task = '保护庄园里的某个秘密'
    alibi = '案发时在厨房准备晚餐'
    motive = '死者拖欠他多年薪水，且知道他的一个致命秘密'
    relationships = @(
        @{target='林默'; relation='对手'}
        @{target='周明远'; relation='同谋'}
    )
}
$script.roles += $r3

$r4 = @{
    name = '周明远'
    age = 30
    occupation = '医生'
    description = '温文尔雅的年轻医生，死者的私人医生'
    background = '被死者资助完成学业，后成为其私人医生'
    secret_task = '掩盖一次医疗事故的证据'
    alibi = '案发时在死者房间进行例行检查'
    motive = '死者发现了他的一次医疗事故，威胁要毁掉他的职业生涯'
    relationships = @(
        @{target='苏婉'; relation='未婚妻'}
        @{target='赵铁柱'; relation='同谋'}
    )
}
$script.roles += $r4

$script.clues = @()
$c1 = @{
    title = '毒药瓶'
    content = '在死者书房的垃圾桶中发现一个小玻璃瓶，残留有剧毒物质'
    is_red_herring = $false
    content_hint = '瓶子上隐约可以看到一个字母 L'
    unlock_phase = 'act1'
}
$script.clues += $c1

$c2 = @{
    title = '通话记录'
    content = '案发时间前后，林默的手机与一个未知号码有长达15分钟的通话'
    target_role = '林默'
    is_red_herring = $false
    content_hint = '这个号码属于一名已离职的庄园员工'
    unlock_phase = 'act1'
}
$script.clues += $c2

$c3 = @{
    title = '遗嘱文件'
    content = '在死者保险柜中发现一份新拟定的遗嘱，将所有财产捐给慈善机构'
    is_red_herring = $true
    content_hint = '遗嘱的日期就在案发前一天'
    unlock_phase = 'act2'
}
$script.clues += $c3

$c4 = @{
    title = '医疗记录'
    content = '一份被篡改的病历记录，显示死者曾出现过中毒症状但被误诊'
    target_role = '周明远'
    is_red_herring = $false
    content_hint = '病历上的签名看起来有些别扭'
    unlock_phase = 'act2'
}
$script.clues += $c4

$c5 = @{
    title = '密信'
    content = '一封藏在画室地板下的信，是苏婉生母生前写给她的'
    target_role = '苏婉'
    is_red_herring = $false
    content_hint = '信中提到了一笔巨额遗产'
    unlock_phase = 'act2'
}
$script.clues += $c5

$script.plot_outline = @{
    act1 = '众人发现富商死在书房，初步调查现场，发现毒药瓶和通话记录。'
    act2 = '深入调查各自背景，发现遗嘱、医疗记录和密信，矛盾激化。'
    act3 = '公开对质，揭示所有秘密，找出真凶。'
}

$script.private_events = @()
$pe1 = @{
    phase = 'act1'
    target_role_name = '林默'
    content = '你发现书房的窗户是开着的——有人在你之前进来过。'
}
$script.private_events += $pe1

$pe2 = @{
    phase = 'act1'
    target_role_name = '苏婉'
    content = '你在画室听到走廊传来急促的脚步声，大约在案发时间。'
}
$script.private_events += $pe2

$pe3 = @{
    phase = 'act2'
    target_role_name = '赵铁柱'
    content = '有人匿名塞了一张纸条到你房间："小心医生"。'
}
$script.private_events += $pe3

$pe4 = @{
    phase = 'act2'
    target_role_name = '周明远'
    content = '你发现管家的房间里有庄园的旧地图，标注了一些隐藏通道。'
}
$script.private_events += $pe4

$json = $script | ConvertTo-Json -Depth 10
""

$filename = "test_script_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$json | Out-File -FilePath $filename -Encoding utf8
Write-Host "[OK] 剧本已保存到: $filename" -ForegroundColor Green
""

if (![string]::IsNullOrWhiteSpace($adminKey)) {
    $url = "http://localhost:8000/api/scripts?admin_key=$adminKey"
    try {
        Write-Host '正在上传剧本...' -ForegroundColor Yellow
        $body = @{
            title = $script.title
            genre = $script.genre
            difficulty = $script.difficulty
            player_count = $script.player_count
            estimated_time = $script.estimated_time
            background_story = $script.background_story
            true_killer = $script.true_killer
            murder_method = $script.murder_method
            cover_up = $script.cover_up
            roles = $script.roles
            clues = $script.clues
            plot_outline = $script.plot_outline
            private_events = $script.private_events
        } | ConvertTo-Json -Depth 10
        $resp = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType 'application/json' -ErrorAction Stop
        Write-Host "[OK] 剧本已上传，ID: $($resp.script_id)" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] 上传失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host '提示: 请确保后端服务已启动 (http://localhost:8000)' -ForegroundColor Yellow
    }
} else {
    Write-Host '提示: 输入管理员密钥可自动上传至后端 API' -ForegroundColor DarkGray
}

""
Write-Host '=== 完成 ===' -ForegroundColor Cyan
