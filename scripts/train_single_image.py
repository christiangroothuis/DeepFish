import sys, os, pprint

path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, path)
from haven import haven_utils as hu
import numpy as np
from DeepFish import datasets, models, wrappers
import argparse
from tqdm.auto import tqdm

from PIL import Image
import matplotlib.pyplot as plt

import torch
from torch.backends import cudnn
from torch import nn
import torchvision.transforms as T
import exp_configs

cudnn.benchmark = True

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--datadir', type=str,
                        default='/mnt/public/datasets/DeepFish')
    parser.add_argument("-e", "--exp_config", default='loc')
    parser.add_argument("-uc", "--use_cuda", type=int, default=1)  # 0 for CPU, 1 for CUDA, 2 for MPS
    args = parser.parse_args()

    print("CUDA availability:", torch.cuda.is_available(),
          "\n Torch CUDA version:", torch.version.cuda)

    if args.use_cuda:
        if torch.cuda.is_available():
            device = 'cuda'
        elif torch.backends.mps.is_available():
            device = 'mps'
        else:
            raise ValueError('Neither CUDA nor MPS is available. Please run with "-uc 0" for CPU mode.')
    else:
        device = 'cpu'

    device = torch.device(device)
    print(f'Running on device: {device}')

    # device = torch.device('cuda' if args.use_cuda else 'cpu')

    exp_dict = exp_configs.EXP_GROUPS[args.exp_config][0]
    train_set = datasets.get_dataset(dataset_name=exp_dict["dataset"],
                                     split="train",
                                     transform=exp_dict.get("transform"),
                                     datadir=args.datadir)

    # Create model, opt, wrapper
    model_original = models.get_model(exp_dict["model"], exp_dict=exp_dict).to(device)
    opt = torch.optim.Adam(model_original.parameters(),
                           lr=1e-5, weight_decay=0.0005)

    model = wrappers.get_wrapper(exp_dict["wrapper"], model=model_original, opt=opt).to(device)

    if args.exp_config == 'loc':
        batch = torch.utils.data.dataloader.default_collate([train_set[3]])
    elif args.exp_config == 'seg':
        batch = torch.utils.data.dataloader.default_collate([train_set[0]])
    elif args.exp_config == 'reg':
        batch = torch.utils.data.dataloader.default_collate([train_set[7]])
    else:
        batch = torch.utils.data.dataloader.default_collate([train_set[10]])

    for e in range(50):
        score_dict = model.train_on_batch(batch)
        print(e, score_dict)

        model.vis_on_batch(batch, f'single_image_{args.exp_config}.png')

        # validate on batch
        val_dict = model.val_on_batch(batch)
        pprint.pprint(val_dict)
