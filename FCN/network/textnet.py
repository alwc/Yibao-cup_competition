import torch.nn as nn
import torch
import torch.nn.functional as F
from network.vgg import VGG16
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
class Upsample(nn.Module):

    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv1x1 = nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.conv3x3 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.deconv = nn.ConvTranspose2d(out_channels, out_channels, kernel_size=4, stride=2, padding=1)

    def forward(self, upsampled, shortcut):
        x = torch.cat([upsampled, shortcut], dim=1)
        x = self.conv1x1(x)
        x = self.conv3x3(x)
        x = self.deconv(x)
        return x

class TextNet(nn.Module):

    def __init__(self, backbone='vgg', output_channel=3):
        super().__init__()

        self.backbone_name = backbone
        self.output_channel = output_channel

        if backbone == 'vgg':
            self.backbone = VGG16()
            self.deconv5 = nn.ConvTranspose2d(512, 512, kernel_size=4, stride=2, padding=1,output_padding=1)
            self.merge4 = Upsample(512 + 512, 256)
            self.merge3 = Upsample(256 + 256, 128)
            self.merge2 = Upsample(128 + 128, 64)
            self.merge1 = Upsample(64 + 64, self.output_channel)
        elif backbone == 'resnet':
            pass

    # torch.Size([4, 64, 200, 200])
    # torch.Size([4, 128, 100, 100])
    # torch.Size([4, 256, 50, 50])
    # torch.Size([4, 512, 25, 25])
    # torch.Size([4, 512, 12, 12])
    def forward(self, x):
        C1, C2, C3, C4, C5 = self.backbone(x)
        up5 = self.deconv5(C5)
        up5 = F.relu(up5)

        up4 = self.merge4(C4, up5)
        up4 = F.relu(up4)

        up3 = self.merge3(C3, up4)
        up3 = F.relu(up3)

        up2 = self.merge2(C2, up3)
        up2 = F.relu(up2)

        up1 = self.merge1(C1, up2)
        return up1

if __name__ == '__main__':
    import torch

    input = torch.randn((1, 3, 400, 400))
    print(input.dtype)
    net = TextNet().cuda()
    print(net(input.cuda()).shape)
    print(net(input.cuda())[:,0].view(-1).shape)
