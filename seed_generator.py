import google.generativeai as genai
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

# Setup
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: No API Key found.")
    exit()

genai.configure(api_key=api_key)

# Dynamic Model Selection
valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
priorities = [
    'gemini-2.5-flash',
    'models/gemini-2.5-flash',
    'gemini-1.5-flash', 
    'gemini-1.5-flash-001', 
    'gemini-pro'
]
selected_model = None
for p in priorities:
    matches = [vm for vm in valid_models if p in vm]
    if matches:
        selected_model = matches[0]
        break
if not selected_model and valid_models:
    selected_model = valid_models[0]
print(f"Selected Model: {selected_model}")
model = genai.GenerativeModel(selected_model)

def generate_batch(batch, level):
    prompt = f"""
    You are a Japanese teacher. Create a JSON dataset for the following {level} grammar points:
    {batch}

    For each point, provide:
    1. "concept": The grammar point name.
    2. "meaning": Core meaning in Traditional Chinese.
    3. "structure": Connection rule.
    4. "explanation": Concise usage explanation in Traditional Chinese.
    5. "level": "{level}"
    6. "tags": "{level}"

    Output strictly a JSON list of objects. No markdown.
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        print(f"Error generating batch: {e}")
        return []

def run_generation(grammar_list, level, filename):
    output_data = []
    batch_size = 5
    print(f"Starting generation for {len(grammar_list)} {level} items...")
    
    for i in range(0, len(grammar_list), batch_size):
        batch = grammar_list[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}: {batch}")
        results = generate_batch(batch, level)
        if results:
            output_data.extend(results)
            print(f"  - Generated {len(results)} items.")
        else:
            print("  - Failed to generate.")
        time.sleep(1)
        
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    print(f"Done! Saved to {filename}")

# --- GRAMMAR LISTS ---

n3_list = [
    "〜合う", "いくら〜ても / どんなに〜ても", "〜一方だ", "〜上に", "〜うちに", "〜おかげで", "〜おきに", "〜おそれがある",
    "お〜だ", "〜がきっかけで", "〜かける", "〜がち", "〜かな", "〜から〜にかけて", "〜からには", "〜かわりに",
    "〜きる", "〜くらい", "〜結果", "〜こそ", "〜こと", "〜ごとに", "〜ことから", "〜ことになっている", "〜ことはない",
    "〜込む", "〜最中に", "〜際に", "〜さえ", "〜さえ〜ば", "〜しかない", "〜じゃない", "〜ずに", "〜せいで",
    "〜たがる", "〜だけ", "〜だけでなく", "たとえ〜ても", "〜たところ", "〜たびに", "〜ために", "〜たものだ",
    "〜だらけ", "〜だろう", "なんて〜だろう", "つい〜てしまう", "ついでに", "〜っけ", "〜つもりだ", "〜ている",
    "〜ている場合じゃない", "〜てからでないと", "〜てしかたがない", "〜て済む", "〜てたまらない", "〜てはいけないから",
    "〜てはじめて", "〜ても構わない", "〜てもしかたがない", "〜ても始まらない", "〜といえば", "〜ということだ",
    "〜というよりも", "〜といっても", "〜通す", "〜とおりに", "〜とか〜とか", "〜としたら", "〜として",
    "〜としても", "〜とたん", "〜途中で", "〜とともに", "〜とのことだ", "〜とは限らない", "〜とみえる",
    "〜なあ", "〜直す", "〜など", "〜において", "〜に限る", "〜にかけては", "〜に代わって", "〜に関して",
    "〜に決まっている", "〜に比べて", "〜にしたがって", "〜にしても", "〜に対して", "〜に違いない", "〜について",
    "〜につき", "〜につれて", "〜にとって", "〜には", "〜に反して", "〜によって", "〜によっては", "〜によると",
    "〜にわたって", "〜のでしょうか", "数量 + は", "〜場合", "〜ばかりなく", "〜はずがない", "〜ば〜のに",
    "〜は別として", "〜はもちろん", "〜ぶり", "〜ふりをする", "〜べきだ", "〜べきだった", "〜ほど",
    "〜ほど〜はない", "まるで〜みたいだ", "まるで〜ようだ", "〜向きに", "〜向けに", "〜も〜ば〜も", "〜ようがない",
    "〜ようとする", "連用中止", "〜わけがない", "〜わけだ", "〜わけではない", "〜わけにはいかない", "〜わりには",
    "〜を込めて", "〜を中心に", "〜を通して"
]

n2_list = [
    "〜あげく", "〜あまり", "あまりの〜に", "〜以上は", "〜一方で", "〜以来", "〜上で", "〜上は",
    "〜得る", "〜折に", "〜かいがあって", "〜限り", "〜がたい", "〜かと思うと", "〜か〜ないかのうちに",
    "〜かねない", "〜かねる", "〜かのようだ", "〜からいうと", "〜からして", "〜からすると", "〜からといって",
    "〜気味", "〜きり", "〜くせに", "〜くらいなら", "〜げ", "〜ことだ", "〜ことだし", "〜ことなく",
    "〜ことだろう", "〜ことになると", "〜ことに", "〜ざるを得ない", "〜次第", "〜次第だ", "〜末に",
    "〜ずじまい", "〜ずにはいられない", "〜そうにない", "〜だけあって", "〜だけに", "〜だけまし", "〜たて",
    "〜たものではない", "〜っこない", "〜つつ", "〜つつある", "〜っぽい", "〜てこのかた", "〜てでも",
    "〜てならない", "〜てはいられない", "〜てまで", "〜てみせる", "〜というものではない", "〜といった", "〜といったら",
    "〜とかで", "〜どころか", "〜ところだった", "〜どころではない", "〜として〜ない", "〜とともに", "〜となると",
    "〜とは", "〜に越したことはない", "〜に応えて", "〜に際して", "〜に限って", "〜に相違ない", "〜にて",
    "〜のみならず", "〜ぱなし", "〜ぶる", "〜ないことには", "〜ないことはない", "〜ないで済む", "〜ないとも限らない",
    "〜ながら", "〜なんて", "〜にあたり", "〜に応じて", "〜に限らず", "〜に限り", "〜に加えて",
    "〜に先立って", "〜にしたら", "〜にしては", "〜に沿って", "〜につき", "〜につけて", "〜にすぎない",
    "〜にともなって", "〜にほかならない", "〜にも関わらず", "〜に基づいて", "〜ぬ", "〜ぬきにして", "〜ぬく",
    "〜の上では", "〜のことだから", "〜のもとで", "〜ばかりか", "〜ばかりだ", "〜ばかりに", "〜はさておき",
    "〜はともかくとして", "〜はまだしも", "〜はもとより", "〜反面", "〜まい", "〜ままに", "〜もかまわず",
    "〜もしない", "〜ものか", "〜ものがある", "〜ものだ", "〜ものだから", "〜ものなら", "〜ものの",
    "〜もん", "〜やら〜やら", "〜ようとしている", "〜ようものなら", "〜を契機に", "〜を頼りに", "〜を問わず",
    "〜を除いて", "〜をはじめ", "〜をめぐって", "〜をもとに", "〜んだから"
]

n1_list = [
    "〜あっての", "〜いかんだ", "〜いかんに関わらず", "〜かたがた", "〜かたわら", "〜がてら", "〜かと思いきや",
    "〜が早いか", "〜からある", "〜かれ〜かれ", "〜きっての", "〜きらいがある", "〜極まる", "〜ごとき",
    "〜こととて", "〜始末だ", "〜ずくめ", "〜ずにはおかない", "〜ずにはすまない", "〜術がない", "〜すら",
    "〜そばから", "ただ〜のみ", "〜たためしがない", "〜たところで", "〜だに", "〜だの〜だの", "〜た弾みに",
    "〜た分だけ", "〜たまでだ", "〜たら最後", "〜たら〜たで", "〜たりとも", "〜たるもの", "〜尽くす",
    "〜つ〜つ", "〜であれ", "〜てからというもの", "〜ではあるまいし", "〜てまえ", "〜てやまない", "〜と相まって",
    "〜とあれば", "〜といい〜といい", "〜といえども", "〜というもの", "〜ときたら", "〜ところを", "〜とはいえ",
    "〜ともあろう", "〜ともなく", "〜ともなると", "〜ながら", "〜なくしては", "〜なくもない", "〜なしに",
    "〜ならでは", "〜ないまでも", "〜なり", "〜なりとも", "〜なり〜なり", "〜なりに", "〜にあって",
    "〜に至る", "〜に言わせれば", "〜にかかっては", "〜に関わる", "〜に限ったことではない", "〜にかこつけて", "〜にかたくない",
    "〜にかまけて", "〜にして", "〜に忍びない", "〜に即して", "〜に堪える", "〜に足る", "〜にとどまらず",
    "〜に則って", "〜にはあたらない", "〜には及ばない", "〜には無理がある", "〜にひきかえ", "〜にもほどがある", "〜にもまして",
    "〜に〜を重ねて", "〜ねばならない", "〜の至り", "〜の極み", "〜のやら", "〜はおろか", "〜ばそれまでだ",
    "〜びる", "〜べからず", "〜べく", "〜ほどのことではない", "〜まじき", "〜までだ", "〜までもない",
    "〜まみれ", "〜めく", "〜もさることながら", "〜もそこそこに", "〜も同然だ", "〜ものを", "〜や否や",
    "〜ゆえに", "〜よう", "〜ようが", "〜ようにも", "〜より", "〜わ〜わで", "〜をおいて",
    "〜を押して", "〜を顧みず", "〜を限りに", "〜を兼ねて", "〜を皮切りに", "〜を禁じ得ない", "〜を境に",
    "〜をもって", "〜をものともせず", "〜を踏まえて", "〜を経て", "〜を余儀なくされる", "〜をよそに", "〜んがために",
    "〜んばかりに"
]

# Run all generations
run_generation(n3_list, "N3", "grammar_n3.json")
run_generation(n2_list, "N2", "grammar_n2.json")
run_generation(n1_list, "N1", "grammar_n1.json")
