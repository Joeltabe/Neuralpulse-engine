import os, sys
os.environ['TRIBE_CACHE_DIR'] = 'E:/tribev2_cache'
sys.path.insert(0, r'E:\Downloads\react\neuralpulse-engine-backend')
from neuromarketing.text_processor import TextFeatureProcessor

tp = TextFeatureProcessor(cache_dir='E:/tribev2_cache')
ok = tp.load()
print(f'Loaded: {ok}')
if ok:
    result = tp.extract_text_features('NeuralPulse is amazing. This text should trigger the brain model prediction pipeline.', frequency=2.0)
    print(f'Has embeddings: {"embeddings" in result}')
    if 'embeddings' in result:
        print(f'Embeddings shape: {result["embeddings"].shape}')
    else:
        print(f'Keys: {list(result.keys()) if result else "empty dict"}')
else:
    print('Failed to load text model')
