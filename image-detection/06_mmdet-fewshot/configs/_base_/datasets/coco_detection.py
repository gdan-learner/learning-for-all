# dataset settings
dataset_type = 'CocoDataset'
data_root = 'data/TianchiAug/'
img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True)
albu_train_transforms = [
    dict(
        type='ShiftScaleRotate',
        shift_limit=0.0625,
        scale_limit=0.0,
        rotate_limit=0,
        interpolation=1,
        p=0.2),
    dict(
        type='RandomBrightnessContrast',
        brightness_limit=[0.1, 0.3],
        contrast_limit=[0.1, 0.3],
        p=0.2),
    dict(
        type='OneOf',
        transforms=[
            dict(
                type='RGBShift',
                r_shift_limit=10,
                g_shift_limit=10,
                b_shift_limit=10,
                p=1.0),
            dict(
                type='HueSaturationValue',
                hue_shift_limit=20,
                sat_shift_limit=30,
                val_shift_limit=20,
                p=1.0)
        ],
        p=0.1),
    dict(type='ChannelShuffle', p=0.1)
]

train_pipeline = [
    # dict(type='Mosaic', img_scale=(2666, 1600), pad_val=114.0),
    # dict(type='MixUp', img_scale=(2666, 1600), ratio_range=(0.8, 1.6), pad_val=114.0),
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(
        type='Resize',
        img_scale=[(1333, 800), (2666, 1600)],
        multiscale_mode='range',
        keep_ratio=True),
    dict(
        type='Albu',
        transforms=albu_train_transforms,
        bbox_params=dict(
            type='BboxParams',
            format='pascal_voc',
            label_fields=['gt_labels'],
            min_visibility=0.0,
            filter_lost_elements=True
        ),
        keymap={
            'img': 'image',
            'gt_bboxes': 'bboxes'
        },
        update_pad_shape=True,
        skip_img_without_anno=True),
    dict(type='RandomFlip', flip_ratio=0.5),
    dict(type='Normalize', **img_norm_cfg),
    dict(type='Pad', size_divisor=32),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels']),
]
val_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=(2000, 1200),
        flip=False,
        transforms=[
            dict(type='Resize', keep_ratio=True),
            dict(type='RandomFlip'),
            dict(type='Normalize', **img_norm_cfg),
            dict(type='Pad', size_divisor=32),
            dict(type='ImageToTensor', keys=['img']),
            dict(type='Collect', keys=['img']),
        ])
]

test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        # img_scale=[(1333, 800), (1333, 864), (1333, 928), (1333, 992),
        #            (1333, 1056), (1333, 1120), (1333, 1184), (1333, 1248)],
        img_scale=[(1333, 800), (1777, 1067), (2222, 1333), (2666, 1600)],
        # img_scale=(1333, 1248),
        flip=True,
        transforms=[
            dict(type='Resize', keep_ratio=True),
            dict(type='RandomFlip'),
            dict(
                type='Normalize',
                mean=[123.675, 116.28, 103.53],
                std=[58.395, 57.12, 57.375],
                to_rgb=True),
            dict(type='Pad', size_divisor=32),
            dict(type='ImageToTensor', keys=['img']),
            dict(type='Collect', keys=['img'])
        ])
]
data = dict(
    samples_per_gpu=4,
    workers_per_gpu=8,
    train=dict(
        type="ClassBalancedDataset",
        oversample_thr=0.002,  # 重采样
        # type='MultiImageMixDataset',
        dataset=dict(
            type=dataset_type,
            ann_file=data_root + 'annotations/instances_trainval.json',
            img_prefix=data_root + 'images/',
            # pipeline=[
            #     dict(type='LoadImageFromFile'),
            #     dict(type='LoadAnnotations', with_bbox=True)
            # ]
            pipeline=train_pipeline
        ),
    ),
    val=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/instances_val2017.json',
        img_prefix=data_root + 'images/',
        pipeline=val_pipeline),
    test=dict(
        type=dataset_type,
        # ann_file='data/val/' + 'annotations/instances_val2017.json',
        ann_file=data_root + 'annotations/instances_val2017.json',
        # img_prefix='data/val/' + 'images/',
        img_prefix=data_root + 'images/',
        pipeline=test_pipeline))
evaluation = dict(interval=1, metric='bbox')
