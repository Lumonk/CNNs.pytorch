# DIY batch-normalization layer 
import torch 
import torch.nn as nn 


class BatchNorm(nn.Module):

    def __init__(self, num_features, eps=1e-5, momentum=0.01, affine=True,
                 track_running_stats=True):
        super(BatchNorm, self).__init__()


        self.num_features = num_features
        self.eps = eps
        self.momentum = momentum
        self.affine = affine
        self.track_running_stats = track_running_stats
        
        if self.affine:
            self.bias = nn.Parameter(torch.Tensor(num_features))
            self.weight = nn.Parameter(torch.Tensor(num_features))
        else:
            self.register_parameter('weights', None)
            self.register_parameter('bias', None)

        if self.track_running_stats:
            self.register_buffer('running_mean', torch.zeros(num_features))
            self.register_buffer('running_var', torch.ones(num_features))
            self.register_buffer('num_batches_tracked', torch.tensor(0, dtype=torch.long))
        else:
            self.register_parameter('running_mean', None)
            self.register_parameter('running_var', None)
            self.register_buffer('num_batches_tracked', None)
        self.reset_parameters()

    def reset_running_stats(self):
        if self.track_running_stats:
            self.running_mean.zero_()
            self.running_var.fill_(1)
            self.num_batches_tracked.zero_()

    def reset_parameters(self):
        self.reset_running_stats()
        if self.affine:
            self.weight.data.fill_(1)
            self.bias.data.zero_()

    def _check_input_dim(self, input):
        if input.dim() != 4:
            raise ValueError('expected 4D input (got {}D input)'
                             .format(input.dim()))

    def forward(self, input):

        if input.dim() == 2 : # linear
            input = input.unsqueeze(-1,).unsqueeze(-1)

        if self.training :
            B, C, H, W = input.shape
            y = input.transpose(0, 1).contiguous() # C x B x H x W
            y = y.view(C, -1)  # C x (BHW)
            mean = y.mean(-1)
            var = y.var(-1, unbiased=False)
            var2 = y.var(-1, unbiased=True)
          
            with torch.no_grad():
                self.running_mean.mul_(1-self.momentum).add_(
                    mean*(self.momentum))
                self.running_var.mul_(1-self.momentum).add_(
                    var2*(self.momentum))

        else :
            mean = self.running_mean
            var = self.running_var


        rsqrt_var = torch.rsqrt(var.view(1, -1, 1, 1)+self.eps)
        out =(input-mean.view(1,-1,1,1)) * rsqrt_var

        if self.affine :
            out = out * self.weight.view(1, -1, 1, 1)
            out = out + self.bias.view(1, -1, 1, 1)
        return out

    def extra_repr(self):
        return '{num_features}, eps={eps}, momentum={momentum}, affine={affine}, ' \
                'track_running_stata={track_running_stats}'.format(**self.__dict__)
