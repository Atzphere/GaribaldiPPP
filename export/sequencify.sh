# todo: make this more abstract and less janky
for outputFolder in */;
do
	echo "sequencifying $outputFolder"
	ffmpeg -r 7 -i "$outputFolder/CASS_10W_%05d.png" 	 -y -c:v libx264 $outputFolder\\temp.mp4
	mv -f ${outputFolder}temp.mp4 ${outputFolder}${outputFolder::-1}.mp4
done

read -rsp $'Press enter to continue...\n'