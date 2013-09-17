hour=`TZ=America/New_York date +%k`
day_part=$((hour/6))

if [ $day_part -eq 0 ]; then
	filename="night"
fi
if [ $day_part -eq 1 ]; then
	filename="morning"
fi
if [ $day_part -eq 2 ]; then
	filename="afternoon"
fi
if [ $day_part -eq 3 ]; then
	filename="evening"
fi
echo $filename