declare -a lastWeek=("$(date +"%Y%m%d")" "$(date -d '-1 day' '+%Y%m%d')" "$(date -d '-2 day' '+%Y%m%d')"
"$(date -d '-3 day' '+%Y%m%d')" "$(date -d '-4 day' '+%Y%m%d')" "$(date -d '-5 day' '+%Y%m%d')" "$(date -d '-6 day' '+%Y%m%d')")
declare -a test

cd /home/aq_dir/geos/BC/ #path to geos data
yourfilenames=`ls *.nc`
j=0
for eachfile in $yourfilenames
do
    for i in "${lastWeek[@]}" ; do

        if [ "$eachfile" == "$i.nc" ]
            then echo "executing your bash script file"
            #./myscript.sh
        else
            echo $j
            test[$j]=$i
            j=$(( $j + 1 ))

        fi

    done
done
if [ $j -ge 0 ]
    then
      for day in "${test[@]}" ;
       do
        echo $(date -d $day +'%Y-%m-%d')
        cd /home/AirQuality-downloadGEOSData/downloadGEOSData/ #path_to_script
        sh downscale.sh $(date -d $day +'%Y-%m-%d')
      done
fi