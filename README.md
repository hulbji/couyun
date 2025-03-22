# 凑韵诗词格律检测工具

余早嗜诗，尝久事白话诗，不至于能，然亦小有所得。然于古韵，仍存敬畏，未敢涉足，盖因音律之道未得其门而入，自觉力有不逮。
后因学东瀛语，始知其字有音读、训读二法，音读中又分吴、汉、唐，皆源自华夏古音，此所谓“域外音”也。各方言、域外音等，虽历经变迁，然于研究古音仍具管窥之效。余由此渐入佳境。
格律者，音之规则也，其抑扬顿挫，华夏千年文化精髓半在其中。今人或有不屑，以为迂腐；或有畏难者，久难入门。所谓“靡不有初，鲜克有终”，如上种种，连“初”都难以迈出，更令人惋惜。 网上阐述格律精妙之处者众多，然余自愧词穷，难以尽述。
近来忽有感悟，近体诗词前有珠玉，今人所作难以企及，但格律规则不过平仄游戏，规则既定，便可作程序判之。遂作一版，以飨诗友。因早有“搜韵网”在前，功能齐全，使用方便。余效仿之，绝不能及。诗友戏称“凑韵”。后屡次更新，以至于此。又作一《六州歌头》。以励余及众诗友：

诗骚并峙，从此鬼神惊。荆榛路，灵均骨，沉汨水，证嘉名。魏晋风霜烈，子建笔，嵇康曲，渊明酒，震雷霆。后人倾。李杜光辉万丈，鲸涛动，鹏翼垂溟。看香山古韵，爱者遍东瀛。诉尽平生。久回萦。
更东坡酹，稼轩剑，易安絮，放翁情。西河忆，甘州望，扬州慨，万调荣。百代风雷荡，昆刀刻，雪泥铭。薪火继，江河涌，待新旌。莫叹焦桐古涩，律中随处有瑶琼。使云笺铺展，椽笔就辰星。试听新声。

## 使用方法：
下载应用程序或运行rhythm.py即可运行。分为3个模块。

### 诗校验：
输入五言或七言的律诗或绝句，选择使用的韵书（默认为平水韵）程序会自动判断其所属的格式，并给出判断结果。输入的诗歌可以带标点以及括号内的注释，程序会自动忽略括号中的内容。并通过以下内容展示。
“〇”当前字平仄正确，“中”当前字属于多音字，“错”当前字平仄正确。如分析杜甫的《绝句》：
> 江碧鸟逾白，山青花欲燃。
> 今春看又过，何日是归年。
>
> 中仄中平仄
> 江碧鸟逾白	
> 〇〇〇〇〇
>
> 平平平仄平
> 山青花欲燃	先韵 押韵 
> 〇〇〇〇〇
>
> 中平平仄仄
> 今春看又过	
> 〇〇中〇中
>
> 中仄仄平平
> 何日是归年	先韵 押韵 
> 〇〇〇〇〇
> 检测完毕，耗时0.00328s

### 词校验
输入一首词，并指定这首词的词牌（一个词牌可能有多种名称，如“贺新郎”又称为“乳燕飞”，“金缕曲”，部分词牌的别名也是支持的），如果词牌无误且内容能够与词牌中的格式匹配，则会展示输出结果，词牌格式依据《钦定词谱》。
如分析李白的《忆秦娥》：
> 箫声咽，秦娥梦断秦楼月。
> 秦楼月，年年柳色，灞陵伤别。
> 乐游原上清秋节，咸阳古道音尘绝。
> 音尘绝，西风残照，汉家陵阙。
>
> 你的格式为 格一
>
> 中中仄韵
> 箫声咽 七部仄、十八部入声、七部平 第一组韵 押韵
> 〇〇中
>
> 中平中仄平平仄韵
> 秦娥梦断秦楼月 十八部入声 第一组韵 押韵
> 〇〇中〇〇〇〇
>
> 平平仄叠
> 秦楼月 十八部入声 第一组韵 押韵
> 〇〇〇
>
> 中中中中句中中平仄韵
> 年年柳色　灞陵伤别 十八部入声 第一组韵 押韵
> 〇〇〇〇　〇〇〇〇
> 
> 中平中仄中平仄韵
> 乐游原上清秋节 十七部入声、十八部入声 第一组韵 押韵
> 〇〇〇〇〇〇〇
> 
> 中平中仄平平仄韵
> 咸阳古道音尘绝 十八部入声 第一组韵 押韵
> 〇〇〇〇〇〇〇
> 
> 平平仄叠
> 音尘绝 十八部入声 第一组韵 押韵
> 〇〇〇
>
> 中平中仄句中平平仄韵
> 西风残照　汉家陵阙 十八部入声 第一组韵 押韵
> 〇〇〇〇　〇〇〇〇
> 检测完毕，耗时0.10645s

### 查字
输入一个汉字，可以查询其在平水韵、词林正韵、中华新韵和中华通韵中的韵部。如查询字“涯”：
> 涯
>
> 涯在：
> 平水韵九佳，词林正韵五部平
> 平水韵九佳，词林正韵十部平