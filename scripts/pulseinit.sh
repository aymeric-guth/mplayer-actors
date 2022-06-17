pulseaudio --kill
pulseaudio --load=module-native-protocol-tcp --exit-idle-time=-1 --daemon
pacmd load-module \
	module-remap-sink \
	sink_name=rear_stereo \
	master=MON_L__MON_R__LINE_3__LINE_4__VIRTUAL_1__VIRTUAL_2__VIRTUAL_3__VIRTUAL_4 \
	channels=8 \
	master_channel_map=mono,mono,mono,mono,mono,mono,mono,mono \
	channel_map=left,right,aux0,aux0,aux0,aux0,aux0,aux0 \
	remix=no
pacmd set-default-sink 2
