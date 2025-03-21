# 凑韵诗词格律检测工具

余早嗜诗，尝久事白话诗，不至于能，然亦小有所得。然于古韵，仍存敬畏，未敢涉足，盖因音律之道未得其门而入，自觉力有不逮。
后因学东瀛语，始知其字有音读、训读二法，音读中又分吴、汉、唐，皆源自华夏古音，此所谓“域外音”也。各方言、域外音等，虽历经变迁，然于研究古音仍具管窥之效。余由此渐入佳境。
格律者，音之规则也，其抑扬顿挫，华夏千年文化精髓半在其中。今人或有不屑，以为迂腐；或有畏难者，久难入门。所谓“靡不有初，鲜克有终”，如上种种，连“初”都难以迈出，更令人惋惜。 网上阐述格律精妙之处者众多，然余自愧词穷，难以尽述。
近来忽有感悟，近体诗词前有珠玉，今人所作难以企及，但格律规则不过平仄游戏，规则既定，便可作程序判之。遂作一版，以飨诗友。因早有“搜韵网”在前，功能齐全，使用方便。余效仿之，绝不能及。诗友戏称“凑韵”。后屡次更新，以至于此。又作一《六州歌头》。以励余及众诗友：

诗骚并峙，从此鬼神惊。荆榛路，灵均骨，沉汨水，证嘉名。魏晋风霜烈，子建笔，嵇康曲，渊明酒，震雷霆。后人倾。李杜光辉万丈，鲸涛动，鹏翼垂溟。看香山古韵，爱者遍东瀛。诉尽平生。久回萦。
更东坡酹，稼轩剑，易安絮，放翁情。西河忆，甘州望，扬州慨，万调荣。百代风雷荡，昆刀刻，雪泥铭。薪火继，江河涌，待新旌。莫叹焦桐古涩，律中随处有瑶琼。使云笺铺展，椽笔就辰星。试听新声。

如需简单使用只需下载couyun文件夹中压缩包内容即可。
## 1.0 内容
随便写着玩的，大伙将就着用。
目前完成了主体内容，可以对大部分情况下近体诗的格律进行检测，同时也可以输入单字查看韵部。
缺陷：可能无法应对太过生僻的汉字。或者在每句第二字时使用了太多多音字的情况下无法辨别句式。无法在孤平、三平尾、三仄尾时提示。
待实现的功能：孤雁出群的检验首句会显示不押韵。无法检测排律，对于诗词的样式无法提示。

Huluebuji 2024.11.29

### 1.0.1 修复内容
修复了平声韵显示时下平韵显示错误的问题。
优化了部分代码，这下不需要将 hanzi_class.py 放在应用文件夹下了。

Huluebuji 2025.1.2

### 1.1.0 更新内容
更新新韵、通韵的检测，单字也可以查看新韵、通韵韵部了。
优化了部分代码。

Huluebuji 2025.1.3

## 1.2.0 更新内容
新增词牌校验。

Huluebuji 2025.3.3

### 1.3.0 更新内容
将原有的所有模块制作为一个图形化交互系统。可以方便地使用。
同时新增了支持孤雁出群式首句检验。现在首句用邻韵也会显示押韵。
已知BUG：
在检查词牌《一七令》《哨遍》时会有文本对不齐的BUG。
检测词牌时使用新韵通韵会将所有的平声视为错。
部分平水韵读音没有收录齐会导致读音判断有误。
诗校验中如果第二字有过多多音字会影响判断，正在思考新的判断方法。

Huluebuji 2025.3.8

### 1.3.1 修复内容
修复了检查词牌《一七令》《哨遍》时会有文本对不齐的BUG。
修复了检测词牌时使用新韵通韵会将所有的平声视为错的BUG。
修改了部分代码，期望其在验证过程中能够正确识别多音字。
平水韵韵表打表需要时间，先不修复，除非遇到特殊字、读音，否则不影响实际体验。
已知BUG：
在判断词牌《减字木兰花》时无法判断用韵情况。
由于这种情况与韵脚全多音字是一样的，大概率需要整体判断而不是基于一个判断标准。决定一起修复。

Huluebuji 2025.3.9

### 1.3.2 修复内容
修复了韵脚全为多音字无法正常判断平仄的情况。
修复了部分词牌无法检测用韵与特殊格式的情况。
更新了平水韵表。

Huluebuji 2025.3.19
