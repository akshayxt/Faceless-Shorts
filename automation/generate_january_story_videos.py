import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"G:\Faceless-Shorts")
AUTO = ROOT / "automation"
QUEUE_PATH = AUTO / "data" / "30day_topic_queue.json"
UPLOAD_Q_PATH = AUTO / "data" / "upload_queue.json"
PROPS_TEMPLATE = AUTO / "templates" / "cartoon_props.js"
NEW_VIDEO_PS1 = ROOT / "skills" / "faceless-shorts" / "scripts" / "new_video.ps1"
RUN_PIPELINE_PS1 = AUTO / "run_pipeline.ps1"
MAKE_THUMB_MJS = AUTO / "make_thumbnail.mjs"
SEO_PY = AUTO / "build_seo_package.py"
PY_VENV = r"C:\Users\Admin\.faceless-shorts\venv\Scripts\python.exe"

IST = timezone(timedelta(hours=5, minutes=30))

JANUARY_31_STORIES = [
    {
        "id": "01_01_27",
        "day": 52,
        "date_str": "01/01/27",
        "category": "moral-story",
        "title": "Leo's Big New Year Goal: Small Steps Make Big Dreams!",
        "thumb_text": "BIG DREAM SECRET!",
        "primary_keyword": "new year moral stories for kids cartoon",
        "supporting_keywords": ["goal setting for children cartoon", "taking small steps moral story", "preschool new year habits"],
        "fact_summary": "Big dreams feel overwhelming when you look at the whole mountain, but taking one tiny positive action every single morning turns small habits into giant achievements.",
        "hook": "Happy New Year! Leo made a huge list of 100 goals, but felt completely stuck! How did 1 tiny step change everything?",
        "publish_slot_est": "2027-01-01T15:30:00-05:00",
        "publish_at_utc": "2027-01-01T20:30:00Z",
        "lines": [
            {"text": "Happy New Year, little explorers! Time for a brand new adventure!", "caps": "*HAPPY New Year, | little *EXPLORERS! | Time for a brand *NEW | *ADVENTURE!"},
            {"text": "Leo made a giant list of one hundred huge New Year goals!", "caps": "Leo made a giant *LIST | of one hundred huge *NEW | Year *GOALS!"},
            {"text": "Learn to juggle, read fifty books, and build a giant treehouse!", "caps": "Learn to *JUGGLE, | read fifty books, and *BUILD | a giant *TREEHOUSE!"},
            {"text": "Looking at the giant list made Leo feel nervous and completely stuck!", "caps": "Looking at the giant *LIST | made Leo feel *NERVOUS | and completely *STUCK!"},
            {"text": "Then his wise teacher said, You don't have to climb the whole mountain today!", "caps": "Then his wise teacher *SAID, | You don't have to climb the *WHOLE | mountain *TODAY!"},
            {"text": "Just take one tiny, joyful step every single morning!", "caps": "Just take one *TINY, | joyful step every *SINGLE | *MORNING!"},
            {"text": "Read one page, practice one throw, and hammer one wooden board!", "caps": "Read one *PAGE, | practice one throw, and *HAMMER | one wooden *BOARD!"},
            {"text": "Tiny daily steps add up to giant superhero dreams!", "caps": "Tiny daily *STEPS | add up to *GIANT | superhero *DREAMS!"},
            {"text": "Start your journey today and subscribe to BabyBeats Rhymo!", "caps": "*START your journey | today and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "02_01_27",
        "day": 53,
        "date_str": "02/01/27",
        "category": "moral-story",
        "title": "The Boy Who Never Cleaned His Room: The Missing Teddy!",
        "thumb_text": "WHERE IS TEDDY?!",
        "primary_keyword": "cleaning up toys story for kids",
        "supporting_keywords": ["tidy up toys cartoon story", "messy bedroom toddler habits", "responsibility story for kids"],
        "fact_summary": "Tossing toys in messy piles buries your favorite treasures and leads to broken parts. Spending just five minutes tidying up creates a calm, happy room where toys stay safe.",
        "hook": "Leo couldn't find his favorite teddy bear anywhere! What happens when toy mountains take over your bedroom?",
        "publish_slot_est": "2027-01-02T15:30:00-05:00",
        "publish_at_utc": "2027-01-02T20:30:00Z",
        "lines": [
            {"text": "Leo loved building block castles, racing cars, and drawing monsters!", "caps": "Leo loved building block *CASTLES, | racing cars, and *DRAWING | *MONSTERS!"},
            {"text": "When playtime ended, he left all his toys scattered across the floor!", "caps": "When playtime *ENDED, | he left all his toys *SCATTERED | across the *FLOOR!"},
            {"text": "At bedtime, his favorite cuddly teddy bear was nowhere to be found!", "caps": "At bedtime, his favorite *CUDDLY | teddy bear was nowhere to *BE | *FOUND!"},
            {"text": "He searched under toy mountains, tripping over plastic bricks and cars!", "caps": "He searched under toy *MOUNTAINS, | tripping over plastic *BRICKS | and *CARS!"},
            {"text": "Ouch! Stepping on scattered toys hurts little feet and breaks things!", "caps": "*OUCH! Stepping on scattered *TOYS | hurts little feet and *BREAKS | *THINGS!"},
            {"text": "Leo turned on the tidy-up music and raced to put toys into their colorful bins!", "caps": "Leo turned on the *TIDY-UP | music and raced to put toys into their *COLORFUL | *BINS!"},
            {"text": "And there at the very bottom was teddy, smiling safe and sound!", "caps": "And there at the very *BOTTOM | was teddy, smiling *SAFE | and *SOUND!"},
            {"text": "Cleaning up your toys keeps your room safe and your treasures protected!", "caps": "Cleaning up your *TOYS | keeps your room safe and your *TREASURES | *PROTECTED!"},
            {"text": "Tidy up with a smile and subscribe to BabyBeats Rhymo!", "caps": "*TIDY up with | a smile and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "03_01_27",
        "day": 54,
        "date_str": "03/01/27",
        "category": "moral-story",
        "title": "Pippin the Bunny Learns to Share: The Big Carrot Picnic!",
        "thumb_text": "SHARING SECRET!",
        "primary_keyword": "learning to share story for toddlers",
        "supporting_keywords": ["sharing is caring cartoon kids", "bunny sharing carrots moral", "preschool friendship story"],
        "fact_summary": "Hoarding treats all to yourself feels lonely in the end, but sharing with friends doubles the smiles and creates friendships that last forever.",
        "hook": "Pippin found the biggest golden carrot in the forest and hid it! Why was eating it all alone so boring?",
        "publish_slot_est": "2027-01-03T15:30:00-05:00",
        "publish_at_utc": "2027-01-03T20:30:00Z",
        "lines": [
            {"text": "Hop, hop, hooray! Pippin the bunny found the biggest golden carrot in the forest!", "caps": "Hop, hop, *HOORAY! | Pippin the bunny found the *BIGGEST | golden carrot in the *FOREST!"},
            {"text": "It was sweet, crunchy, and bright orange! Mine, all mine, he cheered!", "caps": "It was sweet, *CRUNCHY, | and bright orange! Mine, *ALL | mine, he *CHEERED!"},
            {"text": "He hid behind a bush so none of his woodland friends could have a bite!", "caps": "He hid behind a *BUSH | so none of his woodland *FRIENDS | could have a *BITE!"},
            {"text": "He took one bite, then two bites... but eating in secret felt strangely quiet!", "caps": "He took one *BITE, | then two bites... but eating in secret felt *STRANGELY | *QUIET!"},
            {"text": "He looked across the meadow and saw his friends laughing and playing tag!", "caps": "He looked across the *MEADOW | and saw his friends *LAUGHING | and playing *TAG!"},
            {"text": "Pippin carried the big carrot over and snapped it into four juicy slices!", "caps": "Pippin carried the big *CARROT | over and snapped it into four *JUICY | *SLICES!"},
            {"text": "One for squirrel, one for hedgehog, one for puppy, and one for Pippin!", "caps": "One for *SQUIRREL, | one for hedgehog, one for *PUPPY, | and one for *PIPPIN!"},
            {"text": "Sharing treats turned a lonely snack into the best picnic ever!", "caps": "Sharing treats turned a lonely *SNACK | into the *BEST | picnic *EVER!"},
            {"text": "Share the joy and subscribe to BabyBeats Rhymo for daily tales!", "caps": "*SHARE the joy | and *SUBSCRIBE to | *BABYBEATS Rhymo | for daily *TALES!"}
        ]
    },
    {
        "id": "04_01_27",
        "day": 55,
        "date_str": "04/01/27",
        "category": "moral-story",
        "title": "The Little Cloud Afraid of Thunder: Finding Inner Bravery!",
        "thumb_text": "BRAVE CLOUD!",
        "primary_keyword": "overcoming fear story for kids",
        "supporting_keywords": ["bravery cartoon for preschoolers", "afraid of loud noises story", "thunder fear children story"],
        "fact_summary": "Being brave doesn't mean you never feel scared. Bravery is feeling butterflies in your tummy and taking a deep breath anyway.",
        "hook": "Cloudee shook with fear whenever thunder rumbled! How did a tiny raindrop teach him how to be brave?",
        "publish_slot_est": "2027-01-04T15:30:00-05:00",
        "publish_at_utc": "2027-01-04T20:30:00Z",
        "lines": [
            {"text": "High in the blue sky lived Cloudee, a fluffy, gentle little cloud!", "caps": "High in the blue *SKY | lived Cloudee, a fluffy, *GENTLE | little *CLOUD!"},
            {"text": "Whenever storm clouds gathered, a loud BOOM of thunder made Cloudee shake!", "caps": "Whenever storm clouds *GATHERED, | a loud *BOOM of thunder made Cloudee *SHAKE!"},
            {"text": "He hid behind the mountain peaks, wishing he was brave like the mighty wind!", "caps": "He hid behind the mountain *PEAKS, | wishing he was brave like the *MIGHTY | *WIND!"},
            {"text": "Then a tiny raindrop whispered, Being brave doesn't mean having zero fear!", "caps": "Then a tiny raindrop *WHISPERED, | Being brave doesn't mean having *ZERO | *FEAR!"},
            {"text": "Bravery is feeling scared inside, but choosing to take a gentle deep breath anyway!", "caps": "Bravery is feeling scared *INSIDE, | but choosing to take a gentle *DEEP | breath *ANYWAY!"},
            {"text": "Cloudee took a big breath and floated forward to water the thirsty forest flowers!", "caps": "Cloudee took a big *BREATH | and floated forward to water the *THIRSTY | forest *FLOWERS!"},
            {"text": "When the sun shone through his raindrops, a sparkling seven-color rainbow appeared!", "caps": "When the sun shone through his *RAINDROPS, | a sparkling seven-color *RAINBOW | *APPEARED!"},
            {"text": "You are braver than you know whenever you take that first little step!", "caps": "You are braver than you *KNOW | whenever you take that *FIRST | little *STEP!"},
            {"text": "Be brave and subscribe to BabyBeats Rhymo for daily stories!", "caps": "*BE brave and | *SUBSCRIBE to | *BABYBEATS Rhymo | for daily *STORIES!"}
        ]
    },
    {
        "id": "05_01_27",
        "day": 56,
        "date_str": "05/01/27",
        "category": "moral-story",
        "title": "Toby the Puppy & The Broken Flowerpot: Why Truth Wins!",
        "thumb_text": "WHO BROKE IT?!",
        "primary_keyword": "telling the truth story for kids",
        "supporting_keywords": ["honesty moral story for children", "broken vase truth cartoon", "preschool honesty lesson"],
        "fact_summary": "Lies grow like prickly vines that make you feel guilty inside, but telling the truth instantly lifts the heavy rock off your chest and rebuilds trust.",
        "hook": "Crash! Grandma's favorite flowerpot shattered on the kitchen floor! Toby blamed a pretend monster—until this happened!",
        "publish_slot_est": "2027-01-05T15:30:00-05:00",
        "publish_at_utc": "2027-01-05T20:30:00Z",
        "lines": [
            {"text": "Toby the puppy was chasing his bouncy tennis ball through the sunny kitchen!", "caps": "Toby the puppy was *CHASING | his bouncy tennis ball through the *SUNNY | *KITCHEN!"},
            {"text": "Crash! His tail knocked Grandma's favorite yellow flowerpot right off the table!", "caps": "*CRASH! His tail knocked Grandma's | favorite yellow flowerpot *RIGHT | off the *TABLE!"},
            {"text": "When Grandma rushed in, Toby panicked and said, A giant monster did it!", "caps": "When Grandma rushed *IN, | Toby panicked and said, *A | giant monster *DID IT!"},
            {"text": "Grandma looked worried, but Toby's tummy felt tied in an uncomfortable knot!", "caps": "Grandma looked *WORRIED, | but Toby's tummy felt tied in an *UNCOMFORTABLE | *KNOT!"},
            {"text": "Lies feel heavy, like carrying a sharp stone in your shoe all day long!", "caps": "Lies feel *HEAVY, | like carrying a sharp stone in your *SHOE | all day *LONG!"},
            {"text": "Toby walked up, looked Grandma in the eye, and whispered, It was my bouncy ball!", "caps": "Toby walked *UP, | looked Grandma in the eye, and whispered, *IT | was my bouncy *BALL!"},
            {"text": "Grandma gave him a warm hug and said, Accidents happen, but your honesty is golden!", "caps": "Grandma gave him a warm *HUG | and said, Accidents happen, but your *HONESTY | is *GOLDEN!"},
            {"text": "Telling the truth takes courage, but it heals hearts every single time!", "caps": "Telling the truth takes *COURAGE, | but it heals hearts every *SINGLE | *TIME!"},
            {"text": "Stand strong with honesty—subscribe to BabyBeats Rhymo!", "caps": "*STAND strong with | *HONESTY— | *SUBSCRIBE to | *BABYBEATS Rhymo!"}
        ]
    },
    {
        "id": "06_01_27",
        "day": 57,
        "date_str": "06/01/27",
        "category": "moral-story",
        "title": "Milo the Bear Learns to Say Thank You: The Magic Word!",
        "thumb_text": "MAGIC WORD!",
        "primary_keyword": "saying thank you manners for toddlers",
        "supporting_keywords": ["gratitude cartoon for kids", "polite manners moral story", "magic words thank you preschoolers"],
        "fact_summary": "Saying Thank You is like handing someone a warm emotional hug. It shows you appreciate their kindness and makes everyone feel valued.",
        "hook": "Milo grabbed sweet honey and ran without a word! Why did everyone stop smiling until he said the magic word?",
        "publish_slot_est": "2027-01-06T15:30:00-05:00",
        "publish_at_utc": "2027-01-06T20:30:00Z",
        "lines": [
            {"text": "Milo the little bear loved eating delicious berry pies and sweet honeycomb!", "caps": "Milo the little *BEAR | loved eating delicious berry *PIES | and sweet *HONEYCOMB!"},
            {"text": "Whenever friends brought him gifts, Milo snatched them up without saying a word!", "caps": "Whenever friends brought him *GIFTS, | Milo snatched them up without *SAYING | a *WORD!"},
            {"text": "Soon, his friends felt unappreciated and stopped visiting his cozy treehouse!", "caps": "Soon, his friends felt *UNAPPRECIATED | and stopped visiting his *COZY | *TREEHOUSE!"},
            {"text": "Milo felt sad and asked his mama, Why is nobody coming over to play?", "caps": "Milo felt *SAD | and asked his mama, Why is nobody *COMING | over to *PLAY?"},
            {"text": "Mama smiled gently and said, People love sharing when their kindness is recognized!", "caps": "Mama smiled gently and *SAID, | People love sharing when their *KINDNESS | is *RECOGNIZED!"},
            {"text": "Milo baked fresh warm cookies and ran across the forest to say Thank You!", "caps": "Milo baked fresh warm *COOKIES | and ran across the forest to *SAY | Thank *YOU!"},
            {"text": "Thank you for the berries! Thank you for the honey! Thank you for being my friends!", "caps": "Thank you for the *BERRIES! | Thank you for the honey! Thank you for *BEING | my *FRIENDS!"},
            {"text": "Saying Thank You spreads warm sunshine into everyone around you!", "caps": "Saying Thank You spreads warm *SUNSHINE | into everyone *AROUND | *YOU!"},
            {"text": "Practice gratitude every day and subscribe to BabyBeats Rhymo!", "caps": "*PRACTICE gratitude | every day and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "07_01_27",
        "day": 58,
        "date_str": "07/01/27",
        "category": "moral-story",
        "title": "The Impatient Little Snail: Slow and Steady Always Wins!",
        "thumb_text": "TOO FAST?!",
        "primary_keyword": "patience moral story for children",
        "supporting_keywords": ["slow and steady cartoon kids", "impatient snail preschool story", "learning patience moral"],
        "fact_summary": "Rushing through things leads to tripping, making mistakes, and missing the journey. Taking your time with patience helps you finish strong and notice beauty.",
        "hook": "Sammy the Snail wished he was as fast as a rocket! But what happened when the speedy rabbit tripped on the garden path?",
        "publish_slot_est": "2027-01-07T15:30:00-05:00",
        "publish_at_utc": "2027-01-07T20:30:00Z",
        "lines": [
            {"text": "Sammy the snail crawled along the mossy path, inch by steady inch!", "caps": "Sammy the snail crawled along the *MOSSY | path, inch by *STEADY | *INCH!"},
            {"text": "He watched hummingbirds zip and bunnies sprint across the garden grass!", "caps": "He watched hummingbirds *ZIP | and bunnies sprint across the *GARDEN | *GRASS!"},
            {"text": "I want to be fast right now! Sammy grumbled, trying to slide at super speed!", "caps": "I want to be *FAST | right now! Sammy grumbled, trying to *SLIDE | at super *SPEED!"},
            {"text": "Zoom! Speedy rabbit dashed past like a whirlwind, not looking where he was going!", "caps": "*ZOOM! Speedy rabbit dashed *PAST | like a whirlwind, not looking *WHERE | he was *GOING!"},
            {"text": "Whoosh—CRASH! Rabbit tripped over a garden hose and lost his strawberry basket!", "caps": "Whoosh—*CRASH! | Rabbit tripped over a garden hose and *LOST | his strawberry *BASKET!"},
            {"text": "Sammy steadily glided forward, picking up each strawberry with careful care!", "caps": "Sammy steadily glided *FORWARD, | picking up each strawberry with *CAREFUL | *CARE!"},
            {"text": "He delivered the basket safely without bruising a single delicious fruit!", "caps": "He delivered the basket *SAFELY | without bruising a single *DELICIOUS | *FRUIT!"},
            {"text": "Slow and steady finishes the race with patience and excellence!", "caps": "Slow and steady finishes the *RACE | with patience and *EXCELLENCE!"},
            {"text": "Take your time and subscribe to BabyBeats Rhymo for fun learning!", "caps": "*TAKE your time | and *SUBSCRIBE to | *BABYBEATS Rhymo | for fun *LEARNING!"}
        ]
    },
    {
        "id": "08_01_27",
        "day": 59,
        "date_str": "08/01/27",
        "category": "moral-story",
        "title": "Leo's Sticky Monster Hands: Why Washing Hands Is Fun!",
        "thumb_text": "GERM MONSTERS?!",
        "primary_keyword": "hand washing story for kids cartoon",
        "supporting_keywords": ["soap and water germs story", "hygiene habits for toddlers", "washing hands 20 seconds cartoon"],
        "fact_summary": "Invisible bacteria love sticking to dirt and sugar on your fingers. Lathering up soap for 20 seconds creates bubbles that lift germs so water washes them right down the drain.",
        "hook": "Look at your hands after playing! Millions of tiny invisible germ monsters are throwing a party—unless you grab the soap!",
        "publish_slot_est": "2027-01-08T15:30:00-05:00",
        "publish_at_utc": "2027-01-08T20:30:00Z",
        "lines": [
            {"text": "Leo spent the afternoon digging in sandbox castles and painting rainbow posters!", "caps": "Leo spent the afternoon *DIGGING | in sandbox castles and painting *RAINBOW | *POSTERS!"},
            {"text": "Time for lunch! shouted Mom. Leo ran straight to the table to grab a sandwich!", "caps": "Time for *LUNCH! | shouted Mom. Leo ran straight to the *TABLE | to grab a *SANDWICH!"},
            {"text": "Hold on! Look through the magic science magnifying glass at your fingers!", "caps": "Hold *ON! | Look through the magic science magnifying *GLASS | at your *FINGERS!"},
            {"text": "Millions of microscopic germ monsters were doing silly dances on his palms!", "caps": "Millions of microscopic germ *MONSTERS | were doing silly dances on his *PALMS!"},
            {"text": "Leo turned on the warm water tap and pumped out silky, strawberry soap!", "caps": "Leo turned on the warm water *TAP | and pumped out silky, *STRAWBERRY | *SOAP!"},
            {"text": "Scrub the fronts! Scrub the backs! Scrub between the fingers for twenty seconds!", "caps": "Scrub the *FRONTS! | Scrub the backs! Scrub between the *FINGERS | for twenty *SECONDS!"},
            {"text": "Whoosh! The soap bubbles lifted the germ monsters and flushed them away!", "caps": "*WHOOSH! The soap bubbles *LIFTED | the germ monsters and flushed them *AWAY!"},
            {"text": "Clean hands keep your tummy happy, healthy, and ready for delicious meals!", "caps": "Clean hands keep your tummy *HAPPY, | healthy, and ready for *DELICIOUS | *MEALS!"},
            {"text": "Wash up and subscribe to BabyBeats Rhymo for daily health facts!", "caps": "*WASH up and | *SUBSCRIBE to | *BABYBEATS Rhymo | for daily health *FACTS!"}
        ]
    },
    {
        "id": "09_01_27",
        "day": 60,
        "date_str": "09/01/27",
        "category": "moral-story",
        "title": "Bella the Bird Who Wouldn't Try Broccoli: The Green Tree!",
        "thumb_text": "YUCKY OR YUMMY?!",
        "primary_keyword": "picky eater cartoon story for kids",
        "supporting_keywords": ["trying new foods story toddlers", "healthy vegetable cartoon children", "broccoli superpower kids story"],
        "fact_summary": "Your tongue has thousands of taste buds that need a few tries to discover new favorites. Crunchy veggies are packed with vitamins that give your muscles jumping power.",
        "hook": "Bella squawked and refused to eat the little green trees on her plate! What happened when she took just ONE brave little bite?",
        "publish_slot_est": "2027-01-09T15:30:00-05:00",
        "publish_at_utc": "2027-01-09T20:30:00Z",
        "lines": [
            {"text": "Dinner was served, and Bella the bluebird stared down at her plate with big eyes!", "caps": "Dinner was *SERVED, | and Bella the bluebird stared down at her *PLATE | with big *EYES!"},
            {"text": "Eww! Little green broccoli trees! I don't like green foods! she squawked!", "caps": "*EWW! Little green broccoli *TREES! | I don't like green foods! she *SQUAWKED!"},
            {"text": "Have you ever tasted one? asked her papa. No, but it looks weird! Bella replied!", "caps": "Have you ever tasted *ONE? | asked her papa. No, but it looks *WEIRD! | Bella *REPLIED!"},
            {"text": "Papa smiled and said, How do you know if a playground is fun before you slide?", "caps": "Papa smiled and *SAID, | How do you know if a playground is *FUN | before you *SLIDE?"},
            {"text": "Bella took a tiny fork, dipped the broccoli tree in melted cheese, and took a bite!", "caps": "Bella took a tiny *FORK, | dipped the broccoli tree in melted *CHEESE, | and took a *BITE!"},
            {"text": "CRUNCH! It was warm, savory, and super delicious like a crispy party!", "caps": "*CRUNCH! It was warm, *SAVORY, | and super delicious like a crispy *PARTY!"},
            {"text": "Broccoli gives your wings super flying power and strengthens your bones!", "caps": "Broccoli gives your wings super *FLYING | power and strengthens your *BONES!"},
            {"text": "Taking one brave bite can unlock your brand new favorite food!", "caps": "Taking one brave *BITE | can unlock your brand *NEW | favorite *FOOD!"},
            {"text": "Taste new adventures and subscribe to BabyBeats Rhymo!", "caps": "*TASTE new adventures | and *SUBSCRIBE to | *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "10_01_27",
        "day": 61,
        "date_str": "10/01/27",
        "category": "moral-story",
        "title": "The Angry Little Dragon: How Deep Breaths Cool the Fire!",
        "thumb_text": "DRAGON BREATH!",
        "primary_keyword": "calming down anger management kids",
        "supporting_keywords": ["deep breathing cartoon for toddlers", "angry feelings emotional regulation", "dragon cooling down story"],
        "fact_summary": "When big feelings boil like hot lava inside, taking three slow deep breaths sends oxygen to your brain, cooling the fire so you can speak peacefully.",
        "hook": "Steam shot out of Sparky's ears when his block tower fell! Why did screaming make it worse, and what put out the flame?",
        "publish_slot_est": "2027-01-10T15:30:00-05:00",
        "publish_at_utc": "2027-01-10T20:30:00Z",
        "lines": [
            {"text": "Sparky the little dragon was building the tallest marble run in Dragon Valley!", "caps": "Sparky the little *DRAGON | was building the tallest marble *RUN | in Dragon *VALLEY!"},
            {"text": "A sudden gust of wind blew the whole tower down with a loud CLATTER!", "caps": "A sudden gust of *WIND | blew the whole tower down with a loud *CLATTER!"},
            {"text": "Sparky's cheeks puffed up, smoke puffed from his nose, and his temper boiled!", "caps": "Sparky's cheeks puffed *UP, | smoke puffed from his nose, and his *TEMPER | *BOILED!"},
            {"text": "He stomped his feet and was about to roar fire and scorch the grass!", "caps": "He stomped his *FEET | and was about to roar *FIRE | and scorch the *GRASS!"},
            {"text": "His mama gently placed her paw on his shoulder and said, Smell the flowers!", "caps": "His mama gently placed her *PAW | on his shoulder and said, *SMELL | the *FLOWERS!"},
            {"text": "Sparky breathed in through his nose like smelling roses... one, two, three!", "caps": "Sparky breathed in through his *NOSE | like smelling roses... *ONE, | two, *THREE!"},
            {"text": "Then he blew out through his mouth like cooling birthday candles... whooooosh!", "caps": "Then he blew out through his *MOUTH | like cooling birthday candles... *WHOOOOOSH!"},
            {"text": "Three deep breaths cooled the lava in his chest and brought back his bright smile!", "caps": "Three deep breaths cooled the *LAVA | in his chest and brought back his bright *SMILE!"},
            {"text": "Breathe easy and subscribe to BabyBeats Rhymo for daily emotional skills!", "caps": "*BREATHE easy and | *SUBSCRIBE to | *BABYBEATS Rhymo | for daily emotional *SKILLS!"}
        ]
    },
    {
        "id": "11_01_27",
        "day": 62,
        "date_str": "11/01/27",
        "category": "moral-story",
        "title": "Sammy the Squirrel's Lost Acorn: Why Listening Matters!",
        "thumb_text": "LISTEN TO MOM!",
        "primary_keyword": "listening to parents story for kids",
        "supporting_keywords": ["following directions cartoon kids", "listening manners preschool", "squirrel danger story moral"],
        "fact_summary": "Parents give instructions to protect you from dangers you can't see yet. Good listening keeps you safe and happy.",
        "hook": "Mama Squirrel said Don't cross the windy bridge! But Sammy ignored her warning... and look what happened!",
        "publish_slot_est": "2027-01-11T15:30:00-05:00",
        "publish_at_utc": "2027-01-11T20:30:00Z",
        "lines": [
            {"text": "Sammy the squirrel loved leaping from high oak branches across the sunny park!", "caps": "Sammy the squirrel loved *LEAPING | from high oak branches across the *SUNNY | *PARK!"},
            {"text": "Be careful near the windy bridge! warned Mama Squirrel with a loving smile.", "caps": "Be careful near the *WINDY | bridge! warned Mama Squirrel with a *LOVING | *SMILE!"},
            {"text": "I'm a big boy now, I don't need warnings! Sammy chattered, dashing across the planks!", "caps": "I'm a big boy *NOW, | I don't need warnings! Sammy chattered, dashing *ACROSS | the *PLANKS!"},
            {"text": "WHOOSH! A giant gust of winter wind blew his prize acorn right off the edge!", "caps": "*WHOOSH! A giant gust of winter *WIND | blew his prize acorn right *OFF | the *EDGE!"},
            {"text": "Sammy scrambled and slipped, dangling by his tiny front paws!", "caps": "Sammy scrambled and *SLIPPED, | dangling by his tiny *FRONT | *PAWS!"},
            {"text": "Mama swung down with lightning speed, pulling him back to the safe, solid wood!", "caps": "Mama swung down with *LIGHTNING | speed, pulling him back to the safe, *SOLID | *WOOD!"},
            {"text": "Parents give warnings not to stop fun, but to protect you from unseen dangers!", "caps": "Parents give warnings not to stop *FUN, | but to protect you from *UNSEEN | *DANGERS!"},
            {"text": "Sammy hugged Mama tight and promised to always listen to her caring advice!", "caps": "Sammy hugged Mama *TIGHT | and promised to always listen to her *CARING | *ADVICE!"},
            {"text": "Listen and learn—subscribe to BabyBeats Rhymo for daily adventures!", "caps": "*LISTEN and learn— | *SUBSCRIBE to | *BABYBEATS Rhymo | for daily *ADVENTURES!"}
        ]
    },
    {
        "id": "12_01_27",
        "day": 63,
        "date_str": "12/01/27",
        "category": "moral-story",
        "title": "The Kind Elephant & The Tiny Ant: No One Is Too Small!",
        "thumb_text": "TINY HERO!",
        "primary_keyword": "kindness and helping others kids story",
        "supporting_keywords": ["tiny ant big elephant moral", "helping friends cartoon children", "everyone is important story"],
        "fact_summary": "You don't need giant muscles to be a hero. Even the smallest act of kindness or helpful hand can save someone's whole day.",
        "hook": "Barnaby the elephant laughed when tiny Andy the ant offered to be best friends! But who saved Barnaby when he got trapped?",
        "publish_slot_est": "2027-01-12T15:30:00-05:00",
        "publish_at_utc": "2027-01-12T20:30:00Z",
        "lines": [
            {"text": "Barnaby the giant elephant was the strongest, mightiest animal in the jungle!", "caps": "Barnaby the giant *ELEPHANT | was the strongest, mightiest animal *IN | the *JUNGLE!"},
            {"text": "Tiny Andy the ant waved his antennae and chirped, Want to be best friends, giant?", "caps": "Tiny Andy the ant waved his *ANTENNAE | and chirped, Want to be best *FRIENDS, | *GIANT?"},
            {"text": "Barnaby laughed heartily, You are too microscopic to ever help a big elephant like me!", "caps": "Barnaby laughed *HEARTILY, | You are too microscopic to ever help a big *ELEPHANT | like *ME!"},
            {"text": "The next afternoon, Barnaby's heavy leg stepped into a thick tangle of vines!", "caps": "The next afternoon, Barnaby's heavy *LEG | stepped into a thick tangle *OF | *VINES!"},
            {"text": "He pulled and trumpeted in panic, but the sturdy knots grew tighter and tighter!", "caps": "He pulled and trumpeted in *PANIC, | but the sturdy knots grew *TIGHTER | and *TIGHTER!"},
            {"text": "Andy rallied his army of one hundred tiny ants with sharp, helpful jaws!", "caps": "Andy rallied his army of one hundred *TINY | ants with sharp, helpful *JAWS!"},
            {"text": "Snip, snap, crunch! The tiny ants chewed right through the heavy tangled vines!", "caps": "Snip, snap, *CRUNCH! | The tiny ants chewed right through the heavy *TANGLED | *VINES!"},
            {"text": "Barnaby stepped free, bowed low, and learned that nobody is ever too small to help!", "caps": "Barnaby stepped *FREE, | bowed low, and learned that nobody is ever too *SMALL | to *HELP!"},
            {"text": "Help each other every day and subscribe to BabyBeats Rhymo!", "caps": "*HELP each other | every day and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "13_01_27",
        "day": 64,
        "date_str": "13/01/27",
        "category": "moral-story",
        "title": "The Night Leo Met Bedroom Shadows: Night Bravery!",
        "thumb_text": "SHADOW MONSTER?!",
        "primary_keyword": "afraid of the dark bedtime story kids",
        "supporting_keywords": ["bedroom shadows cartoon children", "overcoming bedtime fear story", "flashlight bravery toddlers"],
        "fact_summary": "Dark shadows look scary because your imagination fills in blanks, but shining a little flashlight reveals it's just your friendly coat rack and sweater.",
        "hook": "Shadows danced on Leo's wall like giant spooky claws! But when he clicked on his flashlight, what was really there?",
        "publish_slot_est": "2027-01-13T15:30:00-05:00",
        "publish_at_utc": "2027-01-13T20:30:00Z",
        "lines": [
            {"text": "The bedroom lights clicked off, and Leo pulled the cozy blankets up to his chin!", "caps": "The bedroom lights clicked *OFF, | and Leo pulled the cozy blankets up *TO | his *CHIN!"},
            {"text": "Creak! A giant spiky silhouette stretched across his bedroom closet door!", "caps": "*CREAK! A giant spiky silhouette *STRETCHED | across his bedroom closet *DOOR!"},
            {"text": "Is that a secret clawed monster lurking in the shadows? Leo's heart beat fast!", "caps": "Is that a secret clawed monster *LURKING | in the shadows? Leo's heart *BEAT | *FAST!"},
            {"text": "He reached out his trembling hand and clicked on his little superhero flashlight!", "caps": "He reached out his trembling *HAND | and clicked on his little superhero *FLASHLIGHT!"},
            {"text": "Click! Warm golden light filled the corner, showing his winter jacket and baseball cap!", "caps": "*CLICK! Warm golden light filled the *CORNER, | showing his winter jacket and *BASEBALL | *CAP!"},
            {"text": "The coat rack had cast a funny shadow because the nightlight was low on the floor!", "caps": "The coat rack had cast a funny *SHADOW | because the nightlight was low on the *FLOOR!"},
            {"text": "Shadows look spooky because your imagination tries to fill in the dark spaces!", "caps": "Shadows look spooky because your *IMAGINATION | tries to fill in the dark *SPACES!"},
            {"text": "Whenever you feel scared of shadows, just shine your light and meet the silly truth!", "caps": "Whenever you feel scared of *SHADOWS, | just shine your light and meet the silly *TRUTH!"},
            {"text": "Be brave at bedtime and subscribe to BabyBeats Rhymo!", "caps": "*BE brave at | bedtime and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "14_01_27",
        "day": 65,
        "date_str": "14/01/27",
        "category": "moral-story",
        "title": "The Grumpy Badger Who Found a Smile: Joy Is Contagious!",
        "thumb_text": "PASS THE SMILE!",
        "primary_keyword": "spreading kindness cartoon for kids",
        "supporting_keywords": ["grumpy badger moral story", "smiling is contagious children", "cheering up friends cartoon"],
        "fact_summary": "Frowns push friends away, but giving a genuine smile triggers mirror neurons in others, instantly bouncing happiness right back to you.",
        "hook": "Boris the Badger woke up on the wrong side of the burrow and growled! How did one smiling bunny melt his grumpy heart?",
        "publish_slot_est": "2027-01-14T15:30:00-05:00",
        "publish_at_utc": "2027-01-14T20:30:00Z",
        "lines": [
            {"text": "Boris the badger woke up on the prickly side of his underground den!", "caps": "Boris the badger woke *UP | on the prickly side of his underground *DEN!"},
            {"text": "He scowled at the morning sun and grunted at every animal he passed on the trail!", "caps": "He scowled at the morning *SUN | and grunted at every animal he passed *ON | the *TRAIL!"},
            {"text": "Soon, all the forest birds stopped singing and the chipmunks scurried away into trees!", "caps": "Soon, all the forest birds stopped *SINGING | and the chipmunks scurried away into *TREES!"},
            {"text": "Being grumpy made the whole forest feel chilly, cloudy, and lonely!", "caps": "Being grumpy made the whole *FOREST | feel chilly, cloudy, and *LONELY!"},
            {"text": "Then little Pippin the bunny hopped up and beamed a gigantic, warm, goofy smile!", "caps": "Then little Pippin the bunny hopped *UP | and beamed a gigantic, warm, goofy *SMILE!"},
            {"text": "Boris tried to stay mad, but the cheerful smile tickled his whiskers like warm sunshine!", "caps": "Boris tried to stay *MAD, | but the cheerful smile tickled his whiskers like warm *SUNSHINE!"},
            {"text": "A tiny chuckle escaped his snout, then grew into a roaring belly laugh!", "caps": "A tiny chuckle escaped his *SNOUT, | then grew into a roaring *BELLY | *LAUGH!"},
            {"text": "Smiles are like magic boomerangs—the more you give, the more bounce right back!", "caps": "Smiles are like magic *BOOMERANGS— | the more you give, the more bounce right *BACK!"},
            {"text": "Spread a smile today and subscribe to BabyBeats Rhymo!", "caps": "*SPREAD a smile | today and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "15_01_27",
        "day": 66,
        "date_str": "15/01/27",
        "category": "moral-story",
        "title": "Barnaby Beaver Who Refused to Sleep: Why Bodies Need Rest!",
        "thumb_text": "NO SLEEP TODAY?!",
        "primary_keyword": "importance of sleep story for kids",
        "supporting_keywords": ["why we need sleep cartoon children", "bedtime habits moral story", "tired beaver sleep lesson"],
        "fact_summary": "While you sleep, your brain recharges its memory batteries and your body repairs muscles so you wake up with 100% superhero energy.",
        "hook": "Barnaby wanted to build wooden dams all night long without napping! But why did his legs turn to wobbly jelly the next morning?",
        "publish_slot_est": "2027-01-15T15:30:00-05:00",
        "publish_at_utc": "2027-01-15T20:30:00Z",
        "lines": [
            {"text": "Barnaby the busy beaver wanted to build the tallest wooden dam on the river!", "caps": "Barnaby the busy *BEAVER | wanted to build the tallest wooden dam on the *RIVER!"},
            {"text": "Bedtime! called his parents. But Barnaby insisted, Sleeping is a waste of time!", "caps": "Bedtime! called his *PARENTS. | But Barnaby insisted, Sleeping is a waste of *TIME!"},
            {"text": "He gnawed on birch logs under the moonlight, refusing to close his drooping eyes!", "caps": "He gnawed on birch logs under the *MOONLIGHT, | refusing to close his drooping *EYES!"},
            {"text": "By sunrise, his head felt heavy as a boulder and his paws turned to wobbly jelly!", "caps": "By sunrise, his head felt heavy as a *BOULDER | and his paws turned to wobbly *JELLY!"},
            {"text": "He missed a branch, dropped his favorite chisel, and tumbled splash into the river!", "caps": "He missed a branch, dropped his favorite *CHISEL, | and tumbled splash into the *RIVER!"},
            {"text": "Doctor Owl pulled him ashore and explained, Sleep is your body's charging station!", "caps": "Doctor Owl pulled him *ASHORE | and explained, Sleep is your body's charging *STATION!"},
            {"text": "While you snooze, your brain sorts memories and your muscles rebuild superhero strength!", "caps": "While you snooze, your brain sorts *MEMORIES | and your muscles rebuild superhero *STRENGTH!"},
            {"text": "Barnaby curled up for a cozy eight-hour nap and woke up ready to build world wonders!", "caps": "Barnaby curled up for a cozy eight-hour *NAP | and woke up ready to build world *WONDERS!"},
            {"text": "Recharge your superpower sleep and subscribe to BabyBeats Rhymo!", "caps": "*RECHARGE your superpower | sleep and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "16_01_27",
        "day": 67,
        "date_str": "16/01/27",
        "category": "moral-story",
        "title": "The Little Hedgehog's Prickly Hug: You Are Special!",
        "thumb_text": "PRICKLY HERO!",
        "primary_keyword": "self-esteem and uniqueness story kids",
        "supporting_keywords": ["accepting yourself cartoon kids", "hedgehog quills superpower story", "being different is cool children"],
        "fact_summary": "Everyone is born with different traits. What makes you different isn't a flaw—it's your special superpower that helps you shine.",
        "hook": "Hattie hated her prickly quills because she couldn't give soft hugs! But how did her quills save all her friends from the rolling apple?",
        "publish_slot_est": "2027-01-16T15:30:00-05:00",
        "publish_at_utc": "2027-01-16T20:30:00Z",
        "lines": [
            {"text": "Hattie the little hedgehog looked sadly at her forest friends playing in the clearing!", "caps": "Hattie the little hedgehog looked *SADLY | at her forest friends playing in the *CLEARING!"},
            {"text": "Bunnies had silky fur and puppies had soft paws, but Hattie was covered in stiff quills!", "caps": "Bunnies had silky fur and puppies had soft *PAWS, | but Hattie was covered in stiff *QUILLS!"},
            {"text": "Why can't I be soft and fluffy like everyone else? she sighed to herself!", "caps": "Why can't I be soft and fluffy like everyone *ELSE? | she sighed to *HERSELF!"},
            {"text": "Suddenly, a giant red apple broke loose from the hilltop tree and rolled down fast!", "caps": "Suddenly, a giant red apple broke loose from the *HILLTOP | tree and rolled down *FAST!"},
            {"text": "It bounced straight toward the baby ducks splashing peacefully in the pond!", "caps": "It bounced straight toward the baby ducks *SPLASHING | peacefully in the *POND!"},
            {"text": "Hattie curled into a brave spiky ball and rolled directly into the giant runaway apple!", "caps": "Hattie curled into a brave spiky *BALL | and rolled directly into the giant runaway *APPLE!"},
            {"text": "THUMP! Her sturdy quills pinned the apple instantly, saving all the ducklings!", "caps": "*THUMP! Her sturdy quills pinned the apple *INSTANTLY, | saving all the *DUCKLINGS!"},
            {"text": "What makes you different isn't a mistake—it's your one-of-a-kind superpower!", "caps": "What makes you different isn't a *MISTAKE— | it's your one-of-a-kind *SUPERPOWER!"},
            {"text": "Celebrate being yourself and subscribe to BabyBeats Rhymo!", "caps": "*CELEBRATE being yourself | and *SUBSCRIBE to | *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "17_01_27",
        "day": 68,
        "date_str": "17/01/27",
        "category": "moral-story",
        "title": "Two Little Monkeys & The Golden Swing: Taking Turns!",
        "thumb_text": "MY TURN NOW!",
        "primary_keyword": "taking turns and sharing for kids",
        "supporting_keywords": ["playground manners cartoon toddlers", "fighting over toys moral story", "timer turn taking children"],
        "fact_summary": "Fighting over toys ruins playtime for everyone. Setting a friendly countdown timer to take turns makes games twice as thrilling.",
        "hook": "Pip and Pop tugged on the playground swing until the rope creaked! Why was nobody swinging, and how did a simple timer fix it?",
        "publish_slot_est": "2027-01-17T15:30:00-05:00",
        "publish_at_utc": "2027-01-17T20:30:00Z",
        "lines": [
            {"text": "Pip and Pop the monkey twins raced into the playground to grab the brand new tire swing!", "caps": "Pip and Pop the monkey twins raced into the *PLAYGROUND | to grab the brand new tire *SWING!"},
            {"text": "I got here first! yelled Pip. No, I grabbed the rope first! shouted Pop!", "caps": "I got here *FIRST! | yelled Pip. No, I grabbed the rope *FIRST! | shouted *POP!"},
            {"text": "They pulled and yanked on opposite sides, twisting the rope into an angry tangle!", "caps": "They pulled and yanked on opposite *SIDES, | twisting the rope into an angry *TANGLE!"},
            {"text": "Ten minutes passed, both monkeys were sweaty and red-faced, and nobody was swinging!", "caps": "Ten minutes passed, both monkeys were *SWEATY | and red-faced, and nobody was *SWINGING!"},
            {"text": "Mama Monkey walked over with a fun little sand-timer shaped like a smiling banana!", "caps": "Mama Monkey walked over with a fun little *SAND-TIMER | shaped like a smiling *BANANA!"},
            {"text": "Pip gets three minutes to soar to the clouds, then Pop takes the pilot seat!", "caps": "Pip gets three minutes to soar to the *CLOUDS, | then Pop takes the pilot *SEAT!"},
            {"text": "Pip counted his swings joyfully, and when the timer chimed, handed the swing to Pop!", "caps": "Pip counted his swings joyfully, and when the timer *CHIMED, | handed the swing to *POP!"},
            {"text": "Taking turns turns stubborn arguments into double the laughter and twice the fun!", "caps": "Taking turns turns stubborn arguments into *DOUBLE | the laughter and twice the *FUN!"},
            {"text": "Play nicely together and subscribe to BabyBeats Rhymo!", "caps": "*PLAY nicely together | and *SUBSCRIBE to | *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "18_01_27",
        "day": 69,
        "date_str": "18/01/27",
        "category": "moral-story",
        "title": "The Boastful Rooster: Why True Champions Are Humble!",
        "thumb_text": "I AM BEST?!",
        "primary_keyword": "humility and modesty story for kids",
        "supporting_keywords": ["boastful rooster moral cartoon", "humble champion story children", "good sportsmanship kids"],
        "fact_summary": "Bragging makes others feel small, but cheering for your friends' achievements makes everyone want to celebrate with you.",
        "hook": "Barnaby rooster crowed all day about how high he could flap! What happened when the quiet duck did a graceful backflip into the pond?",
        "publish_slot_est": "2027-01-18T15:30:00-05:00",
        "publish_at_utc": "2027-01-18T20:30:00Z",
        "lines": [
            {"text": "Reggie the red rooster strutted on the barnyard fence, puffing out his glossy chest!", "caps": "Reggie the red rooster strutted on the barnyard *FENCE, | puffing out his glossy *CHEST!"},
            {"text": "I have the loudest crow, the brightest feathers, and the highest jumps in town! he bragged!", "caps": "I have the loudest crow, the brightest *FEATHERS, | and the highest jumps in town! he *BRAGGED!"},
            {"text": "Whenever his friends made great paintings or built castles, Reggie criticized them!", "caps": "Whenever his friends made great *PAINTINGS | or built castles, Reggie criticized *THEM!"},
            {"text": "Nobody likes playing with someone who always insists they are better than everyone!", "caps": "Nobody likes playing with someone who always insists *THEY | are better than *EVERYONE!"},
            {"text": "At the county fair race, Reggie tripped over his own big spurs and landed in mud!", "caps": "At the county fair race, Reggie tripped over his own big *SPURS | and landed in *MUD!"},
            {"text": "Instead of laughing at him, his barnyard friends helped him up and cleaned his feathers!", "caps": "Instead of laughing at him, his barnyard friends *HELPED | him up and cleaned his *FEATHERS!"},
            {"text": "Reggie blushed and realized true greatness means lifting others up with cheer!", "caps": "Reggie blushed and realized true *GREATNESS | means lifting others up with *CHEER!"},
            {"text": "Be humble, cheer for your teammates, and let your kindness speak for itself!", "caps": "Be humble, cheer for your *TEAMMATES, | and let your kindness speak for *ITSELF!"},
            {"text": "Cheer for your friends and subscribe to BabyBeats Rhymo!", "caps": "*CHEER for your friends | and *SUBSCRIBE to | *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "19_01_27",
        "day": 70,
        "date_str": "19/01/27",
        "category": "moral-story",
        "title": "Leo & The Lost Library Book: Keeping Promises!",
        "thumb_text": "PROMISE SECRET!",
        "primary_keyword": "keeping promises and responsibility kids",
        "supporting_keywords": ["library book care cartoon kids", "trustworthiness moral story children", "keeping your word toddlers"],
        "fact_summary": "Your word is your bond. When you promise to care for borrowed books or toys, returning them safe builds ironclad trust with everyone.",
        "hook": "Leo promised Ms. Maple he would protect the shiny dinosaur book! But where did he leave it when playtime started?",
        "publish_slot_est": "2027-01-19T15:30:00-05:00",
        "publish_at_utc": "2027-01-19T20:30:00Z",
        "lines": [
            {"text": "Leo checked out a spectacular book about roaring dinosaurs from the library!", "caps": "Leo checked out a spectacular book about roaring *DINOSAURS | from the *LIBRARY!"},
            {"text": "I promise to keep it dry, clean, and return it on Friday! Leo told Librarian Owl.", "caps": "I promise to keep it dry, clean, and return it on *FRIDAY! | Leo told Librarian *OWL!"},
            {"text": "On Thursday afternoon, he tossed the book into the wet grass while chasing a soccer ball!", "caps": "On Thursday afternoon, he tossed the book into the wet *GRASS | while chasing a soccer *BALL!"},
            {"text": "Dark storm clouds rolled in, and raindrops began splashing onto the colorful pages!", "caps": "Dark storm clouds rolled *IN, | and raindrops began splashing onto the colorful *PAGES!"},
            {"text": "Leo remembered his promise, dove across the lawn, and shielded the book with his coat!", "caps": "Leo remembered his promise, dove across the *LAWN, | and shielded the book with his *COAT!"},
            {"text": "He dried the cover with a soft towel, placed it safely in his backpack, and returned it on time!", "caps": "He dried the cover with a soft towel, placed it safely in his *BACKPACK, | and returned it on *TIME!"},
            {"text": "Librarian Owl stamped his card with a gold star and said, You are someone we can trust!", "caps": "Librarian Owl stamped his card with a gold *STAR | and said, You are someone we can *TRUST!"},
            {"text": "Keeping your promises is like building an invisible bridge of trust that never breaks!", "caps": "Keeping your promises is like building an invisible bridge of *TRUST | that never *BREAKS!"},
            {"text": "Keep your word and subscribe to BabyBeats Rhymo for daily stories!", "caps": "*KEEP your word | and *SUBSCRIBE to | *BABYBEATS Rhymo | for daily *STORIES!"}
        ]
    },
    {
        "id": "20_01_27",
        "day": 71,
        "date_str": "20/01/27",
        "category": "moral-story",
        "title": "Penny Penguin's First Day at Preschool: Making Friends!",
        "thumb_text": "NEW FRIENDS!",
        "primary_keyword": "first day of school bravery cartoon kids",
        "supporting_keywords": ["making friends at preschool story", "shy penguin first day cartoon", "social confidence for toddlers"],
        "fact_summary": "Everyone feels butterflies on their first day. Walking up with a smile and saying 'Hi, want to build blocks?' turns strangers into buddies.",
        "hook": "Penny hid behind her mommy's flipper on the first morning of snow school! How did one blue crayon help her make three best friends?",
        "publish_slot_est": "2027-01-20T15:30:00-05:00",
        "publish_at_utc": "2027-01-20T20:30:00Z",
        "lines": [
            {"text": "Penny the penguin held her father's flipper tight as they walked to the preschool door!", "caps": "Penny the penguin held her father's flipper *TIGHT | as they walked to the preschool *DOOR!"},
            {"text": "Her tummy did backflips and she worried, What if nobody wants to play with me?", "caps": "Her tummy did backflips and she *WORRIED, | What if nobody wants to play with *ME?"},
            {"text": "Inside the classroom, animals were singing songs, stacking blocks, and coloring murals!", "caps": "Inside the classroom, animals were singing *SONGS, | stacking blocks, and coloring *MURALS!"},
            {"text": "Penny stood shyly in the corner until she noticed a bear cub trying to build an igloo!", "caps": "Penny stood shyly in the corner until she noticed a bear cub trying to build an *IGLOO!"},
            {"text": "She took a deep breath, smiled brightly, and said, Hi, my name is Penny! Can I help you?", "caps": "She took a deep breath, smiled brightly, and *SAID, | Hi, my name is Penny! Can I help *YOU?"},
            {"text": "The cub beamed and handed her a big blue ice block! They laughed and built an arctic fortress!", "caps": "The cub beamed and handed her a big blue ice *BLOCK! | They laughed and built an arctic *FORTRESS!"},
            {"text": "Making a friend starts with just three magical words: Hi, want to play?", "caps": "Making a friend starts with just three magical *WORDS: | Hi, want to *PLAY?"},
            {"text": "Everyone feels shy sometimes, but a friendly smile opens doors to wonderful friendships!", "caps": "Everyone feels shy sometimes, but a friendly smile opens doors to *WONDERFUL | *FRIENDSHIPS!"},
            {"text": "Make new friends and subscribe to BabyBeats Rhymo!", "caps": "*MAKE new friends | and *SUBSCRIBE to | *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "21_01_27",
        "day": 72,
        "date_str": "21/01/27",
        "category": "moral-story",
        "title": "Felix Fox & The Glowing Tablet: Nature Is Fun!",
        "thumb_text": "SCREEN TIME TRAP!",
        "primary_keyword": "screen time balance cartoon for kids",
        "supporting_keywords": ["unplug and play outside story", "too much screen time kids cartoon", "healthy habits outdoor play"],
        "fact_summary": "Digital screens are fun in small doses, but running outside, catching mud bugs, and climbing hills makes your body strong and happy.",
        "hook": "Felix tapped his glowing tablet for hours until his eyes got red and scratchy! What amazing secret was waiting outside in the meadow?",
        "publish_slot_est": "2027-01-21T15:30:00-05:00",
        "publish_at_utc": "2027-01-21T20:30:00Z",
        "lines": [
            {"text": "Felix the fox was glued to his shiny video game tablet from sunrise to sunset!", "caps": "Felix the fox was glued to his shiny video game *TABLET | from sunrise to *SUNSET!"},
            {"text": "Tap, swipe, click! His eyes were red, his neck was stiff, and his paws were crampy!", "caps": "Tap, swipe, *CLICK! | His eyes were red, his neck was stiff, and his paws were *CRAMPY!"},
            {"text": "Come chase autumn leaves and climb the mossy rocks! called his woodland friends!", "caps": "Come chase autumn leaves and climb the mossy *ROCKS! | called his woodland *FRIENDS!"},
            {"text": "Just five more minutes! mumbled Felix, staring at colorful digital pixels on the glass.", "caps": "Just five more minutes! mumbled *FELIX, | staring at colorful digital pixels on the *GLASS!"},
            {"text": "Mama Fox announced screen time is over, placed the tablet in the basket, and led him outside!", "caps": "Mama Fox announced screen time is over, placed the tablet in the *BASKET, | and led him *OUTSIDE!"},
            {"text": "The fresh pine breeze woke his senses, and the squishy grass tickled his furry paws!", "caps": "The fresh pine breeze woke his *SENSES, | and the squishy grass tickled his furry *PAWS!"},
            {"text": "They built a giant leaf fort, caught dandelion seeds, and raced up the sunny hill!", "caps": "They built a giant leaf fort, caught dandelion *SEEDS, | and raced up the sunny *HILL!"},
            {"text": "Screen time is fun in small doses, but real outdoor adventures make your body strong and happy!", "caps": "Screen time is fun in small doses, but real outdoor adventures make your body *STRONG | and *HAPPY!"},
            {"text": "Unplug and play outside—subscribe to BabyBeats Rhymo!", "caps": "*UNPLUG and play | outside— *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "22_01_27",
        "day": 73,
        "date_str": "22/01/27",
        "category": "moral-story",
        "title": "Tommy Turtle Who Kept Falling: Practice Makes Perfect!",
        "thumb_text": "DON'T GIVE UP!",
        "primary_keyword": "growth mindset resilience story kids",
        "supporting_keywords": ["practice makes progress cartoon children", "turtle learning to roller skate", "never give up story toddlers"],
        "fact_summary": "Nobody is born knowing how to ride a bike or draw stars. Falling down is just your brain discovering what to adjust next time.",
        "hook": "Tommy wobbled on his new roller skates and bonked his shell five times! Did he pack up and quit, or try one more time?",
        "publish_slot_est": "2027-01-22T15:30:00-05:00",
        "publish_at_utc": "2027-01-22T20:30:00Z",
        "lines": [
            {"text": "Tommy the turtle got a shiny pair of four-wheeled roller skates for his birthday!", "caps": "Tommy the turtle got a shiny pair of four-wheeled *ROLLER | skates for his *BIRTHDAY!"},
            {"text": "He pushed off the porch, wobbled sideways, and BONK! fell flat on his hard shell!", "caps": "He pushed off the porch, wobbled sideways, and *BONK! | fell flat on his hard *SHELL!"},
            {"text": "I'm clumsy, I have zero balance, I quit! Tommy grumbled, wiping away a tear!", "caps": "I'm clumsy, I have zero balance, I *QUIT! | Tommy grumbled, wiping away a *TEAR!"},
            {"text": "Wise Badger rolled over smoothly and said, Nobody is born an Olympic roller champion!", "caps": "Wise Badger rolled over smoothly and said, Nobody is born an Olympic *ROLLER | *CHAMPION!"},
            {"text": "Every time you stumble and fall, your brain muscles learn how to balance better next time!", "caps": "Every time you stumble and fall, your brain muscles learn how to balance *BETTER | next *TIME!"},
            {"text": "Tommy strapped on his helmet, tightened his knee pads, and tried taking two small glides!", "caps": "Tommy strapped on his helmet, tightened his knee *PADS, | and tried taking two small *GLIDES!"},
            {"text": "Gliding left, gliding right! By evening, he was coasting down the path with the wind in his face!", "caps": "Gliding left, gliding right! By evening, he was coasting down the path with the *WIND | in his *FACE!"},
            {"text": "Mistakes are not stopping signs—they are stepping stones toward becoming amazing!", "caps": "Mistakes are not stopping signs—they are stepping stones toward *BECOMING | *AMAZING!"},
            {"text": "Never give up and subscribe to BabyBeats Rhymo for daily encouragement!", "caps": "*NEVER give up | and *SUBSCRIBE to | *BABYBEATS Rhymo | for daily *ENCOURAGEMENT!"}
        ]
    },
    {
        "id": "23_01_27",
        "day": 74,
        "date_str": "23/01/27",
        "category": "moral-story",
        "title": "The Greedy Hamster's Stash: Giving Feels Better!",
        "thumb_text": "ALL FOR ME?!",
        "primary_keyword": "generosity moral story for children",
        "supporting_keywords": ["greedy hamster sharing cartoon", "joy of giving kids story", "preschool generosity lesson"],
        "fact_summary": "Stuffing all the seeds into your own cheeks makes your mouth hurt, but baking seed muffins for your forest friends warms your heart.",
        "hook": "Harry the hamster hid 500 sunflower seeds in his secret burrow! Why did having all the seeds make him feel so empty inside?",
        "publish_slot_est": "2027-01-23T15:30:00-05:00",
        "publish_at_utc": "2027-01-23T20:30:00Z",
        "lines": [
            {"text": "Harry the hamster discovered a secret meadow bursting with thousands of sunflower seeds!", "caps": "Harry the hamster discovered a secret meadow bursting with thousands of *SUNFLOWER | *SEEDS!"},
            {"text": "He stuffed his cheeks until they were round balloons and carted all five hundred seeds home!", "caps": "He stuffed his cheeks until they were round balloons and carted all five hundred *SEEDS | *HOME!"},
            {"text": "He piled them in his underground vault and locked the door with a sturdy wooden twig!", "caps": "He piled them in his underground vault and locked the door with a *STURDY | wooden *TWIG!"},
            {"text": "Sitting on a giant mountain of seeds in the dark, his tummy felt full but his heart felt empty!", "caps": "Sitting on a giant mountain of seeds in the dark, his tummy felt full but his heart felt *EMPTY!"},
            {"text": "Outside, winter winds were blowing cold and his forest friends had very little to eat!", "caps": "Outside, winter winds were blowing cold and his forest friends had *VERY | little to *EAT!"},
            {"text": "Harry loaded a wooden wheelbarrow and delivered baskets of roasted seeds to every den!", "caps": "Harry loaded a wooden wheelbarrow and delivered baskets of roasted seeds to *EVERY | *DEN!"},
            {"text": "The forest erupted in cheerful songs, and they invited Harry to a warm winter feast!", "caps": "The forest erupted in cheerful songs, and they invited Harry to a warm *WINTER | *FEAST!"},
            {"text": "Hoarding things brings worry, but sharing your abundance fills your life with true warmth!", "caps": "Hoarding things brings worry, but sharing your abundance fills your life with *TRUE | *WARMTH!"},
            {"text": "Give generously and subscribe to BabyBeats Rhymo!", "caps": "*GIVE generously and | *SUBSCRIBE to | *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "24_01_27",
        "day": 75,
        "date_str": "24/01/27",
        "category": "moral-story",
        "title": "Charlie Cat Forgot to Say Please: The Courtesy Key!",
        "thumb_text": "MAGIC PLEASE!",
        "primary_keyword": "saying please manners for preschoolers",
        "supporting_keywords": ["magic word please cartoon kids", "polite communication story children", "kitten manners moral"],
        "fact_summary": "Demanding things makes people feel ordered around, but saying 'Please' shows respect and unlocks doors with cheerful smiles.",
        "hook": "Charlie yowled Gimme milk right now! But the bowl stayed empty! What happened when he used the gentle magic word?",
        "publish_slot_est": "2027-01-24T15:30:00-05:00",
        "publish_at_utc": "2027-01-24T20:30:00Z",
        "lines": [
            {"text": "Charlie the kitten jumped onto the dining table and yowled, Gimme a bowl of warm milk!", "caps": "Charlie the kitten jumped onto the dining table and yowled, Gimme a bowl of *WARM | *MILK!"},
            {"text": "He tapped his paws impatiently, but Mama Cat kept quietly reading her morning paper!", "caps": "He tapped his paws impatiently, but Mama Cat kept quietly reading her *MORNING | *PAPER!"},
            {"text": "I said give it to me right now! hissed Charlie, puffing up his gray tail!", "caps": "I said give it to me right now! hissed *CHARLIE, | puffing up his gray *TAIL!"},
            {"text": "Mama looked over her glasses and asked, What happened to your golden manners key?", "caps": "Mama looked over her glasses and asked, What happened to your golden *MANNERS | *KEY?"},
            {"text": "Barking orders makes people feel bossed around and closes their willingness to help!", "caps": "Barking orders makes people feel bossed around and closes their *WILLINGNESS | to *HELP!"},
            {"text": "Charlie sat down neatly, tucked his tail around his paws, and said softly, Please, Mama?", "caps": "Charlie sat down neatly, tucked his tail around his paws, and said softly, *PLEASE, | *MAMA?"},
            {"text": "Mama beamed, poured a creamy dish of milk with cinnamon, and stroked his furry ears!", "caps": "Mama beamed, poured a creamy dish of milk with cinnamon, and stroked his *FURRY | *EARS!"},
            {"text": "The word Please is a magical golden key that opens hearts with kindness and respect!", "caps": "The word Please is a magical golden key that opens hearts with *KINDNESS | and *RESPECT!"},
            {"text": "Unlock good manners every day with BabyBeats Rhymo!", "caps": "*UNLOCK good manners | every day with | *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "25_01_27",
        "day": 76,
        "date_str": "25/01/27",
        "category": "moral-story",
        "title": "The Little Fawn Who Wandered: Always Stay in Sight!",
        "thumb_text": "STAY CLOSE!",
        "primary_keyword": "safety awareness staying with parents kids",
        "supporting_keywords": ["staying safe in public places cartoon", "fawn getting lost moral story", "holding hands safety toddlers"],
        "fact_summary": "The big grocery store or park is exciting, but holding hands or staying where parents can see you keeps you safe from getting lost.",
        "hook": "Daisy the fawn chased a sparkly blue butterfly away from the herd! What should you do if you look up and can't see mom?",
        "publish_slot_est": "2027-01-25T15:30:00-05:00",
        "publish_at_utc": "2027-01-25T20:30:00Z",
        "lines": [
            {"text": "Daisy the spotted fawn skipped through the spring meadow alongside her watchful mother!", "caps": "Daisy the spotted fawn skipped through the spring meadow alongside her *WATCHFUL | *MOTHER!"},
            {"text": "A sparkly turquoise butterfly fluttered past, dancing from daisy to bluebell flower!", "caps": "A sparkly turquoise butterfly fluttered *PAST, | dancing from daisy to bluebell *FLOWER!"},
            {"text": "Daisy chased the fluttery wings, leaping over logs and deeper into the unfamiliar woods!", "caps": "Daisy chased the fluttery wings, leaping over logs and deeper into the *UNFAMILIAR | *WOODS!"},
            {"text": "When the butterfly flew away, Daisy looked around—the trees were tall, dark, and strange!", "caps": "When the butterfly flew away, Daisy looked around—the trees were tall, dark, *AND | *STRANGE!"},
            {"text": "Mama! she cried, her little heart thumping like a drum! She couldn't see the herd!", "caps": "Mama! she cried, her little heart thumping like a *DRUM! | She couldn't see the *HERD!"},
            {"text": "Remembering safety rules, Daisy stopped moving, stayed by a big oak, and called out loud!", "caps": "Remembering safety rules, Daisy stopped moving, stayed by a big oak, and *CALLED | out *LOUD!"},
            {"text": "Mama Deer heard her voice, dashed through the thicket, and nuzzled her baby safe and warm!", "caps": "Mama Deer heard her voice, dashed through the thicket, and nuzzled her baby *SAFE | and *WARM!"},
            {"text": "Always hold hands in big crowds and stay where parents can clearly see your face!", "caps": "Always hold hands in big crowds and stay where parents can clearly see your *SMILING | *FACE!"},
            {"text": "Stay safe and smart—subscribe to BabyBeats Rhymo!", "caps": "*STAY safe and | smart— *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "26_01_27",
        "day": 77,
        "date_str": "26/01/27",
        "category": "moral-story",
        "title": "The Loud Little Parrot: Learning Your Inside Voice!",
        "thumb_text": "INSIDE VOICE!",
        "primary_keyword": "inside voices manners for toddlers",
        "supporting_keywords": ["library manners cartoon children", "loud parrot quiet voice story", "situational awareness kids"],
        "fact_summary": "Outside is for shouting, racing, and cheering, but inside cozy rooms, gentle voices protect ears and let everyone think and read peacefully.",
        "hook": "Polly squawked like a megaphone inside the quiet library! Why was everyone holding their ears, and how did she learn whisper power?",
        "publish_slot_est": "2027-01-26T15:30:00-05:00",
        "publish_at_utc": "2027-01-26T20:30:00Z",
        "lines": [
            {"text": "Polly the colorful parrot loved exercising her vocal cords at maximum volume!", "caps": "Polly the colorful parrot loved exercising her vocal cords at *MAXIMUM | *VOLUME!"},
            {"text": "She flew into the cozy public library and squawked, HELLO EVERYONE, LOOK AT MY FEATHERS!", "caps": "She flew into the cozy public library and squawked, HELLO EVERYONE, *LOOK | AT MY *FEATHERS!"},
            {"text": "Ears hurt, books rattled, and sleeping baby squirrels woke up crying in fright!", "caps": "Ears hurt, books rattled, and sleeping baby squirrels woke up crying in *FRIGHT!"},
            {"text": "Librarian Owl held up a gentle wing and explained the difference between voice spaces!", "caps": "Librarian Owl held up a gentle wing and explained the difference between *VOICE | *SPACES!"},
            {"text": "The wide open playground is for booming cheering, shouting goals, and loud laughter!", "caps": "The wide open playground is for booming cheering, shouting goals, and *LOUD | *LAUGHTER!"},
            {"text": "Inside cozy rooms, gentle voices protect people's focus and create peaceful spaces!", "caps": "Inside cozy rooms, gentle voices protect people's focus and create *PEACEFUL | *SPACES!"},
            {"text": "Polly leaned in and practiced her warm, gentle whisper voice: Want to read together?", "caps": "Polly leaned in and practiced her warm, gentle whisper *VOICE: | Want to read *TOGETHER?"},
            {"text": "Knowing when to be quiet and when to be loud shows respect for everyone around you!", "caps": "Knowing when to be quiet and when to be loud shows respect for *EVERYONE | around *YOU!"},
            {"text": "Use your gentle voice and subscribe to BabyBeats Rhymo!", "caps": "*USE your gentle | voice and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "27_01_27",
        "day": 78,
        "date_str": "27/01/27",
        "category": "moral-story",
        "title": "Leo's Collapsing Wooden Castle: Mistakes Help Us Grow!",
        "thumb_text": "TOWER CRASH!",
        "primary_keyword": "learning from mistakes cartoon for kids",
        "supporting_keywords": ["building blocks castle collapse moral", "growth mindset architecture story kids", "resilience after failure toddlers"],
        "fact_summary": "When your building blocks tumble down, it's not a failure—it's gravity showing you that castles need a wide, solid base first.",
        "hook": "CRASH! Leo's 10-story block tower collapsed into a heap of pieces! Did he kick the blocks away in tears, or discover an architect secret?",
        "publish_slot_est": "2027-01-27T15:30:00-05:00",
        "publish_at_utc": "2027-01-27T20:30:00Z",
        "lines": [
            {"text": "Leo spent two hours carefully balancing wooden blocks into a magnificent twenty-story castle!", "caps": "Leo spent two hours carefully balancing wooden blocks into a magnificent twenty-story *CASTLE!"},
            {"text": "He reached for the final golden spire at the very top... CRASH! The tower collapsed!", "caps": "He reached for the final golden spire at the very top... *CRASH! | The tower *COLLAPSED!"},
            {"text": "Blocks scattered in every direction! Leo felt hot tears in his eyes and wanted to stomp them!", "caps": "Blocks scattered in every direction! Leo felt hot tears in his eyes and wanted to *STOMP | *THEM!"},
            {"text": "His grandfather knelt beside the wooden rubble and asked, What did the blocks teach you?", "caps": "His grandfather knelt beside the wooden rubble and asked, What did the blocks *TEACH | *YOU?"},
            {"text": "Leo looked at the floor: the base was narrow and thin like a pencil!", "caps": "Leo looked at the floor: the base was narrow and thin like a *PENCIL!"},
            {"text": "Castles need a wide, rock-solid foundation to hold up heavy grand towers above!", "caps": "Castles need a wide, rock-solid foundation to hold up heavy grand *TOWERS | *ABOVE!"},
            {"text": "Leo laid down eight wide blocks on the carpet, rebuilding the strongest castle in history!", "caps": "Leo laid down eight wide blocks on the carpet, rebuilding the strongest *CASTLE | in *HISTORY!"},
            {"text": "Mistakes are not failures—they are secret clues that show you how to build better next time!", "caps": "Mistakes are not failures—they are secret clues that show you how to build *BETTER | next *TIME!"},
            {"text": "Build your wisdom and subscribe to BabyBeats Rhymo!", "caps": "*BUILD your wisdom | and *SUBSCRIBE to | *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "28_01_27",
        "day": 79,
        "date_str": "28/01/27",
        "category": "moral-story",
        "title": "The Interrupting Owl: How Good Listeners Win Hearts!",
        "thumb_text": "LET THEM SPEAK!",
        "primary_keyword": "active listening manners for children",
        "supporting_keywords": ["interrupting conversations cartoon kids", "good listener owl story", "respectful talking manners toddlers"],
        "fact_summary": "Waiting for friends to finish speaking shows you care about their thoughts. Being a good listener makes people love talking with you.",
        "hook": "Ollie the owl hooted over everyone's stories before they could finish! Why did his animal friends stop sharing secrets with him?",
        "publish_slot_est": "2027-01-28T15:30:00-05:00",
        "publish_at_utc": "2027-01-28T20:30:00Z",
        "lines": [
            {"text": "Ollie the young owl knew fascinating facts about stars, acorns, and forest geography!", "caps": "Ollie the young owl knew fascinating facts about stars, acorns, and forest *GEOGRAPHY!"},
            {"text": "Whenever a friend began telling a story, Ollie hooted right over them to share his thoughts!", "caps": "Whenever a friend began telling a story, Ollie hooted right over them to share *HIS | *THOUGHTS!"},
            {"text": "Yesterday I found a cool pebble—began mouse! WELL I FOUND A METEORITE! shouted Ollie!", "caps": "Yesterday I found a cool pebble—began mouse! WELL I FOUND A *METEORITE! | shouted *OLLIE!"},
            {"text": "Soon, his animal friends felt unheard and stopped inviting Ollie to their fireside chats!", "caps": "Soon, his animal friends felt unheard and stopped inviting Ollie to their *FIRESIDE | *CHATS!"},
            {"text": "Wise Grandpa Owl told him, You have two big ears and only one beak for a very good reason!", "caps": "Wise Grandpa Owl told him, You have two big ears and only one beak for a very *GOOD | *REASON!"},
            {"text": "Listening carefully lets you discover amazing things you never would have known on your own!", "caps": "Listening carefully lets you discover amazing things you never would have known on *YOUR | *OWN!"},
            {"text": "At the next campfire, Ollie waited patiently, nodding along as mouse finished her story!", "caps": "At the next campfire, Ollie waited patiently, nodding along as mouse finished *HER | *STORY!"},
            {"text": "Being a great listener makes people feel valued and turns casual buddies into best friends!", "caps": "Being a great listener makes people feel valued and turns casual buddies into *BEST | *FRIENDS!"},
            {"text": "Listen with your heart and subscribe to BabyBeats Rhymo!", "caps": "*LISTEN with your | heart and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "29_01_27",
        "day": 80,
        "date_str": "29/01/27",
        "category": "moral-story",
        "title": "The Sad Puppy Who Got a Warm Hug: Comforting a Friend!",
        "thumb_text": "HUG POWER!",
        "primary_keyword": "empathy and comforting friends for kids",
        "supporting_keywords": ["puppy lost ball comforting story", "how to help sad friends cartoon", "power of hugs empathy preschoolers"],
        "fact_summary": "When someone drops their ice cream or feels sad, sitting beside them and offering a gentle hug releases calming hormones that heal their heart.",
        "hook": "Buster dropped his shiny red ball in the deep mud and whined sadly! What did Leo do to make Buster's tail wag again?",
        "publish_slot_est": "2027-01-29T15:30:00-05:00",
        "publish_at_utc": "2027-01-29T20:30:00Z",
        "lines": [
            {"text": "Buster the little puppy was tossing his favorite red bouncy ball in the park!", "caps": "Buster the little puppy was tossing his favorite red bouncy *BALL | in the *PARK!"},
            {"text": "Plop! The ball rolled straight into a murky mud puddle and sank out of reach!", "caps": "*PLOP! The ball rolled straight into a murky mud puddle and sank out of *REACH!"},
            {"text": "Buster sat on the grass, whimpered softly, and let his floppy ears droop down in sadness!", "caps": "Buster sat on the grass, whimpered softly, and let his floppy ears droop down in *SADNESS!"},
            {"text": "Leo noticed his friend's tears from across the playground and hurried over!", "caps": "Leo noticed his friend's tears from across the playground and hurried *OVER!"},
            {"text": "He didn't say Stop crying or It's just a toy! He simply sat beside Buster on the grass!", "caps": "He didn't say Stop crying or It's just a toy! He simply sat beside Buster on the *GRASS!"},
            {"text": "Leo wrapped his arms around Buster in a warm, gentle, reassuring hug!", "caps": "Leo wrapped his arms around Buster in a warm, gentle, reassuring *HUG!"},
            {"text": "A warm hug releases calming happy hormones that soothe racing hearts and bring peace!", "caps": "A warm hug releases calming happy hormones that soothe racing hearts and bring *PEACE!"},
            {"text": "Buster licked Leo's cheek, wagged his tail, and together they fished the muddy ball out!", "caps": "Buster licked Leo's cheek, wagged his tail, and together they fished the muddy *BALL | *OUT!"},
            {"text": "Comfort your friends and subscribe to BabyBeats Rhymo for daily kindness!", "caps": "*COMFORT your friends | and *SUBSCRIBE to | *BABYBEATS Rhymo | for daily *KINDNESS!"}
        ]
    },
    {
        "id": "30_01_27",
        "day": 81,
        "date_str": "30/01/27",
        "category": "moral-story",
        "title": "The Little Bear Who Brushed Like a Champion: Clean Teeth!",
        "thumb_text": "BRUSH HERO!",
        "primary_keyword": "brushing teeth cartoon routine toddlers",
        "supporting_keywords": ["sugar bugs teeth brushing story", "dental hygiene cartoon for kids", "healthy teeth morning bedtime habit"],
        "fact_summary": "Brushing for two full minutes morning and night washes away plaque monsters and keeps your smile sparkling white and cavity-free.",
        "hook": "Barnaby the bear raced to bed without brushing his teeth! Who came knocking at midnight with tiny pickaxes?",
        "publish_slot_est": "2027-01-30T15:30:00-05:00",
        "publish_at_utc": "2027-01-30T20:30:00Z",
        "lines": [
            {"text": "Barnaby the little bear loved eating sweet berries, crunchy honey-toast, and dried apples!", "caps": "Barnaby the little bear loved eating sweet berries, crunchy honey-toast, and dried *APPLES!"},
            {"text": "When bedtime arrived, Barnaby crawled under his quilt without visiting the bathroom sink!", "caps": "When bedtime arrived, Barnaby crawled under his quilt without visiting the bathroom *SINK!"},
            {"text": "Skipping brushing leaves tiny sugary crumbs wedged between teeth where germs party!", "caps": "Skipping brushing leaves tiny sugary crumbs wedged between teeth where germs *PARTY!"},
            {"text": "In his dream, tiny Sugar Bugs with little pickaxes began drilling holes in white enamel shields!", "caps": "In his dream, tiny Sugar Bugs with little pickaxes began drilling holes in white *ENAMEL | *SHIELDS!"},
            {"text": "Barnaby woke up with a start, jumped out of bed, and reached for his superhero toothbrush!", "caps": "Barnaby woke up with a start, jumped out of bed, and reached for his superhero *TOOTHBRUSH!"},
            {"text": "Brush top teeth! Brush bottom teeth! Brush the chewing surfaces for two full minutes!", "caps": "Brush top teeth! Brush bottom teeth! Brush the chewing surfaces for two full *MINUTES!"},
            {"text": "Frothy minty bubbles scrubbed every single sugar bug down the shiny drain pipe!", "caps": "Frothy minty bubbles scrubbed every single sugar bug down the shiny drain *PIPE!"},
            {"text": "Brushing morning and night keeps your smile sparkling bright, fresh, and cavity-free!", "caps": "Brushing morning and night keeps your smile sparkling bright, fresh, and *CAVITY-FREE!"},
            {"text": "Brush like a champion and subscribe to BabyBeats Rhymo!", "caps": "*BRUSH like a champion | and *SUBSCRIBE to | *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "31_01_27",
        "day": 82,
        "date_str": "31/01/27",
        "category": "moral-story",
        "title": "Leo's Cozy Bedtime Routine: Sweet Dreams Every Night!",
        "thumb_text": "SWEET DREAMS!",
        "primary_keyword": "bedtime routine sleep story for kids",
        "supporting_keywords": ["peaceful bedtime routine cartoon", "gratitude sleep story toddlers", "sweet dreams children animation"],
        "fact_summary": "Warm pajamas, bedtime stories, and gentle hugs help your heartbeat slow down, ushering your mind into magical, happy dreamland.",
        "hook": "The stars are twinkling outside your bedroom window! How does Leo's 3-step cozy bedtime routine turn sleep into an adventure?",
        "publish_slot_est": "2027-01-31T15:30:00-05:00",
        "publish_at_utc": "2027-01-31T20:30:00Z",
        "lines": [
            {"text": "The moon rose high and twinkling stars began dancing across the dark velvet sky!", "caps": "The moon rose high and twinkling stars began dancing across the dark velvet *SKY!"},
            {"text": "Time for Leo's three-step cozy bedtime routine that turns sleep into an adventure!", "caps": "Time for Leo's three-step cozy bedtime routine that turns sleep into an *ADVENTURE!"},
            {"text": "Step one: Warm bubble bath that relaxes tired muscles after a busy day of playing!", "caps": "Step one: Warm bubble bath that relaxes tired muscles after a busy day of *PLAYING!"},
            {"text": "Step two: Snuggle into soft flannel pajamas and read two magical bedtime stories!", "caps": "Step two: Snuggle into soft flannel pajamas and read two magical bedtime *STORIES!"},
            {"text": "Step three: Share three things you were grateful for today with a loving bedtime hug!", "caps": "Step three: Share three things you were grateful for today with a loving bedtime *HUG!"},
            {"text": "Gratitude calms your nervous system, slowing down heartbeat into deep peaceful rhythm!", "caps": "Gratitude calms your nervous system, slowing down heartbeat into deep peaceful *RHYTHM!"},
            {"text": "Head on the pillow, eyes closed, drifting on fluffy clouds toward magical dreamland!", "caps": "Head on the pillow, eyes closed, drifting on fluffy clouds toward magical *DREAMLAND!"},
            {"text": "Sleep well, little dreamers, tomorrow is full of brand new discoveries and joy!", "caps": "Sleep well, little dreamers, tomorrow is full of brand new discoveries and *JOY!"},
            {"text": "Sweet dreams from all of us—subscribe to BabyBeats Rhymo!", "caps": "*SWEET dreams from | all of us— *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    }
]


def update_topic_queue(topics_to_add: list[dict]):
    if QUEUE_PATH.exists():
        q = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    else:
        q = {"channel": "BabyBeats Rhymo", "topics": []}
    topics = q.setdefault("topics", [])
    for nt in topics_to_add:
        existing = next((t for t in topics if t["id"] == nt["id"]), None)
        item_data = {
            "id": nt["id"],
            "day": nt["day"],
            "category": nt["category"],
            "title": nt["title"],
            "thumb_text": nt["thumb_text"],
            "primary_keyword": nt["primary_keyword"],
            "supporting_keywords": nt["supporting_keywords"],
            "score_breakdown": {
                "audience_demand": 19,
                "recent_growth": 18,
                "competition_opportunity": 15,
                "audience_curiosity": 17,
                "click_potential": 9,
                "retention_potential": 9,
                "production_feasibility": 5,
                "niche_relevance": 5
            },
            "total_score": 97,
            "fact_summary": nt["fact_summary"],
            "sources": [
                "https://kidshealth.org",
                "https://www.zerotothree.org"
            ],
            "hook": nt["hook"],
            "visual_focus": "expressive cartoon mascot characters learning emotional skills and moral lessons",
            "status": "ready_for_upload"
        }
        if existing:
            existing.update(item_data)
        else:
            topics.append(item_data)
    QUEUE_PATH.write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {QUEUE_PATH} with {len(topics_to_add)} story topics.")


def build_shots_for_story(nt: dict) -> str:
    thumb_badge = nt.get("thumb_text", "LIFE LESSON!").replace("'", "")
    lines = nt["lines"]
    shot_blocks = []
    
    scenes = [
        ("story_intro", "room", f"K.room(); P.kidCartoon(540, 860, 1.65 * eob(seg(lt, 0, 0.35)), {{ mood: 'happy', t }}); K.pill('{thumb_badge}', 540, 315, 42, C.red, C.white, eob(seg(lt, 0.25, 0.6))); K.burst(540, 740, 1.1, 0.5);", "cue(st, 'whoosh'); cue(st + 0.4, 'pop');"),
        ("problem", "blank", "fillAll('#FEF2F2'); P.kidCartoon(380, 860, 1.55, { mood: 'lookDown', t }); K.pill('UH OH!', 540, 310, 44, C.red, C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.3, 'alarm', { dur: 0.6 });"),
        ("shock", "room", "K.room(); P.kidCartoon(540, 860, 1.6, { mood: 'shock', t }); K.shockLines(540, 740, 240, clamp((lt - 0.4) * 3)); K.pill('WHAT NOW?!', 540, 310, 44, C.yellow, C.ink, 1);", "cue(st, 'alarm', { dur: 0.8 });"),
        ("discovery", "blank", "fillAll('#FFFBEB'); P.creatureBuddy(540, 770, 1.8 * eob(seg(lt, 0, 0.35)), t, '#0284C7'); K.pill('WISE LESSON!', 540, 305, 42, C.ink, C.yellow, 1);", "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle');"),
        ("action_step", "blank", "fillAll('#EFF6FF'); P.batteryMeter(540, 760, 1.45, 1.0); K.pill('SUPER POWER!', 540, 310, 44, C.ink, C.yellow, 1);", "cue(st, 'whoosh'); cue(st + 0.3, 'pop');"),
        ("kindness", "room", "K.room(); P.kidCartoon(380, 860, 1.5, { mood: 'happy', t }); P.creatureBuddy(720, 820, 1.4, t, '#F97316'); K.pill('SHARING JOY!', 540, 310, 44, '#2A9D8F', C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle');"),
        ("heart_moment", "room", "K.room(); P.kidCartoon(540, 840, 1.65, { mood: 'happy', t }); K.heart(540, 520, 2.0 * eob(seg(lt, 0.2, 0.6)), Math.abs(Math.sin(lt * 6))); K.pill('HEART WARM!', 540, 310, 44, '#2A9D8F', C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.3, 'boing');"),
        ("moral_truth", "blank", "fillAll('#F0FDF4'); P.kidCartoon(360, 860, 1.45, { mood: 'happy', t }); P.magnifier(720, 680, 155); K.pill('BIG TRUTH!', 540, 310, 44, '#15803D', C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.35, 'pop');"),
        ("outro", "room", "K.room(); P.kidCartoon(540, 840, 1.65, { mood: 'happy', t }); K.pill('BABYBEATS RHYMO!', 540, 315, 46, C.ink, C.yellow, eob(seg(lt, 0, 0.4))); K.heart(820, 560, 1.35 * eob(seg(lt, 0.3, 0.7)), Math.abs(Math.sin(lt * 8)));", "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.2 });")
    ]

    for i in range(len(lines)):
        name, bg, code, sfx = scenes[i % len(scenes)]
        if i == len(lines) - 1:
            name, bg, code, sfx = scenes[-1]
        shot_blocks.append(f"""  {{
    const st = cut({i});
    add({{
      id: 'S{i+1:02d}', at: st, cam: [540, 800], note: 'scene {name}',
      draw(lt, d, t) {{
        {code}
      }}
    }});
    {sfx}
  }}""")

    return f"""import {{ ctx, C, W, H, TAU, clamp, lerp, seg, eo, eio, eob, rnd, bigText, fillAll, rr, circle, ell, line }} from './core/lib.js';
import {{ L, Le, Wd, T }} from './core/timing.js';
import * as K from './core/kit.js';
import * as P from './cartoon_props.js';

export function buildShots() {{
  const S = [], CUES = [];
  const add = (o) => (S.push(o), o);
  const cue = (t, type, o = {{}}) => CUES.push({{ t: +t.toFixed(3), type, ...o }});
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);

{chr(10).join(shot_blocks)}

  return {{ shots: S, cues: CUES }};
}}
"""


def append_upload_queue(entry: dict):
    if UPLOAD_Q_PATH.exists():
        data = json.loads(UPLOAD_Q_PATH.read_text(encoding="utf-8"))
    else:
        data = {"channel_id": "UCR-Di4-tEAdUM7oPzlGn-vg", "items": []}
    items = data.setdefault("items", [])
    existing = next((it for it in items if it.get("id") == entry["id"]), None)
    if existing:
        existing.update(entry)
    else:
        items.append(entry)
    UPLOAD_Q_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def generate_single_short(nt: dict):
    tid = nt["id"]
    proj_name = f"{tid}_short"
    proj_dir = ROOT / "videos" / proj_name
    print(f"\n========================================================")
    print(f"GENERATING [{nt['day']}/82]: {proj_name} ({nt['title']})")
    print(f"========================================================")

    if not proj_dir.exists():
        cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(NEW_VIDEO_PS1),
            "-Style", "inside-out", "-Name", proj_name, "-Dir", str(ROOT / "videos")
        ]
        subprocess.run(cmd, check=True)

    # Copy cartoon props
    shutil.copyfile(PROPS_TEMPLATE, proj_dir / "src" / "cartoon_props.js")

    # Script json
    script = {
        "title": nt["title"],
        "thumb_text": nt["thumb_text"],
        "voice": "am_puck",
        "speed": 1.05,
        "music": "bed",
        "lead": 0.35,
        "gap": 0.25,
        "outro": 0.85,
        "sources": ["https://kidshealth.org", "https://www.zerotothree.org"],
        "lines": nt["lines"]
    }
    (proj_dir / "script.json").write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

    # Shots js
    (proj_dir / "src" / "shots.js").write_text(build_shots_for_story(nt), encoding="utf-8")

    # SEO & Thumbnail
    (proj_dir / "renders").mkdir(exist_ok=True)
    seo_out = proj_dir / "seo_package.json"
    thumb_out = proj_dir / "renders" / f"{tid}_thumb.jpg"
    mp4_out = proj_dir / "renders" / f"{tid}_short.mp4"

    print("-> Building SEO package...")
    subprocess.run([PY_VENV, str(SEO_PY), "--topic-id", tid, "--out", str(seo_out)], check=True)

    if not thumb_out.exists():
        print("-> Rendering 1280x720 Thumbnail...")
        thumb_created = False
        for attempt in range(1, 4):
            try:
                subprocess.run(
                    ["node", str(MAKE_THUMB_MJS), str(thumb_out), nt["thumb_text"], nt["category"], "BABYBEATS RHYMO"],
                    check=True,
                    timeout=60
                )
                if thumb_out.exists() and thumb_out.stat().st_size > 1000:
                    thumb_created = True
                    break
            except Exception as e:
                if thumb_out.exists() and thumb_out.stat().st_size > 1000:
                    print(f"   [note] Thumbnail file created successfully despite process exit code: {thumb_out.name}")
                    thumb_created = True
                    break
                print(f"   [warn] Thumbnail attempt {attempt}/3 failed: {e}")
                time.sleep(3)
        if not thumb_created:
            print("   [warn] Retrying thumbnail with fallback simple render if needed...")
            if not thumb_out.exists():
                raise RuntimeError(f"Failed to generate thumbnail for {tid}")
    else:
        print(f"-> Thumbnail already exists: {thumb_out.name}")

    if not mp4_out.exists():
        print("-> Executing Audio Synthesis & Video Pipeline (Kokoro + Whisper + Chrome + ffmpeg)...")
        pipe_cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(RUN_PIPELINE_PS1),
            "-ProjectDir", str(proj_dir),
            "-OutVideo", str(mp4_out),
            "-SheetStep", "2", "-SheetCols", "5"
        ]
        subprocess.run(pipe_cmd, check=True)
    else:
        print(f"-> MP4 already exists: {mp4_out.name}")

    # Verify with ffprobe
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,width,height", "-of", "json", str(mp4_out)],
        capture_output=True, text=True, check=True
    )
    info = json.loads(probe.stdout)
    vstream = next((s for s in info.get("streams", []) if s.get("width")), {})
    if int(vstream.get("width", 0)) != 1080 or int(vstream.get("height", 0)) != 1920:
        raise RuntimeError(f"Unexpected dimensions: {vstream}")
    meta = {
        "duration_sec": round(float(info["format"]["duration"]), 2),
        "size_bytes": int(info["format"]["size"]),
        "width": vstream["width"],
        "height": vstream["height"]
    }
    print(f"VERIFIED MP4: {mp4_out.name} ({meta['duration_sec']}s, {meta['size_bytes']} bytes)")

    seo = json.loads(seo_out.read_text(encoding="utf-8"))
    upload_entry = {
        "id": proj_name,
        "topic_id": tid,
        "format": "short",
        "scheduled_slot_est": "15:30 EST",
        "title": seo.get("selected_title") or nt["title"],
        "video_path": str(mp4_out),
        "thumb_path": str(thumb_out),
        "seo_path": str(seo_out),
        "made_for_kids": True,
        "category_id": "27",
        "status": "READY_FOR_UPLOAD",
        "youtube_video_id": None,
        "youtube_url": None,
        "scheduled_publish_est": nt["publish_slot_est"],
        "publish_at": nt["publish_at_utc"],
        "video_specs": meta,
        "updated_at_ist": datetime.now(IST).isoformat()
    }
    append_upload_queue(upload_entry)
    print(f"SUCCESS: Added {proj_name} to upload_queue.json as READY_FOR_UPLOAD (publish_at: {nt['publish_at_utc']})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1, help="Start index (1-based)")
    parser.add_argument("--end", type=int, default=len(JANUARY_31_STORIES), help="End index (1-based)")
    args = parser.parse_args()

    selected = JANUARY_31_STORIES[args.start - 1 : args.end]
    update_topic_queue(selected)
    total = len(selected)
    for i, nt in enumerate(selected, 1):
        print(f"\n>>> PROCESSING STORY VIDEO {i}/{total}: {nt['id']}_short <<<")
        generate_single_short(nt)
    print("\n========================================================")
    print(f"ALL {total} JANUARY STORY VIDEOS GENERATED SUCCESSFULLY!")
    print("========================================================")


if __name__ == "__main__":
    main()
